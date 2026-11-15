"""L-84: a shot call reads whole files through the hooks. The stand-in model answers 'how is it run' from the
attached first 800 characters when the run line is there, and otherwise calls read_file, as the real model may."""
import asyncio, sys, pathlib, json, glob
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _serve import served, CHROME, HERE
from playwright.async_api import async_playwright
ROOT = HERE.parents[2]
mock = open(HERE / 'mockdb.js').read()
SAMPLE = r"""window.__calls=0;window.__reads=[];window.claude={use:async function(n){ if(n==="db")return window.__mockdb; if(n!=="sample")return null;
 var f=async function(input,opts){window.__calls++;var p=String(input),tool=function(n){return (opts.tools||[]).find(function(t){return t.name===n})};
   var qs=p.split("=== ATTACHED")[0].split("\n").filter(function(l){return /^\d+\. tools\//.test(l)});
   var lines=[];for(var i=0;i<qs.length;i++){var file=qs[i].match(/^\d+\. (tools\/\S+?):/)[1],base=file.split("/").pop();
     var att=(p.split("=== "+file+" (first")[1]||"").split("\n=== ")[0],re=new RegExp("(python3|bash) tools/"+base.replace(/\./g,"\\.")+"[^\\n]*"),m=att.match(re),via="head";
     if(!m&&tool("read_file")){var full=await tool("read_file").execute({path:file});window.__reads.push(file);m=full.match(re);via="read_file"}
     lines.push((i+1)+": "+base+" runs as "+(m?m[0].trim():"(not found)")+" ["+via+"]")}
   return {text:lines.join("\n"),truncated:false};}; f.json=null; return f;}};"""
async def main(BASE):
    files = sorted(p.replace(str(ROOT) + "/", "") for p in glob.glob(str(ROOT / "tools/*.py")) + glob.glob(str(ROOT / "tools/*.sh")))
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"]); ctx = await b.new_context(); await ctx.add_init_script(mock + SAMPLE)
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
        await pg.goto(BASE + "/index.html"); await pg.wait_for_timeout(300)
        doc = {"id": "T1", "from": "cloud", "to": "page", "subject": "tools", "body": "x", "ts": 1, "sent_at": "x",
               "asks": [{"n": i + 1, "body": "%s: in one plain sentence, what does this tool do, and how is it run?" % f} for i, f in enumerate(files)]}
        await pg.evaluate("d=>window.__mockdb.doc('mail/'+d.id).set(d)", doc)
        await pg.wait_for_function("Object.values(window.__store).some(function(v){return v.kind==='shot-result'&&v.re==='T1'})", timeout=60000)
        await pg.wait_for_function("document.getElementById('go').textContent==='Ask'", timeout=30000)
        st = await pg.evaluate("window.__store"); r = [v for v in st.values() if v.get("kind") == "shot-result"][0]
        ans = [x["body"] for v in st.values() if v.get("replies") for x in v["replies"]]
        found = sum(1 for a in ans if "(not found)" not in a); viaread = sum(1 for a in ans if "[read_file]" in a and "(not found)" not in a)
        reads = await pg.evaluate("window.__reads")
        note = [l for l in (await pg.inner_text("#msgs")).split("\n") if "hooks run:" in l][-1]
        print("%d tools: state %s | run line found %d/%d (%d of them only after read_file) | read_file calls %d | prov tool_calls %s | commit %s | %s"
              % (len(files), r["state"], found, len(ans), viaread, len(reads), r["prov"].get("tool_calls"), r["prov"].get("commit"), note[note.index("Stop hook"):]))
        print("not found:", [a.split(" runs")[0] for a in ans if "(not found)" in a], "| js errors:", errs or "none")
        await b.close()
with served() as BASE:
    asyncio.run(main(BASE))
