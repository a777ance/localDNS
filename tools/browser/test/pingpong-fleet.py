"""Throughput: one shot of every doc title, a named model, four calls at once (the haiku superfleet)."""
import asyncio, sys, pathlib, json, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _serve import served, CHROME, HERE
from playwright.async_api import async_playwright
ROOT = HERE.parents[2]
mock = open(HERE / 'mockdb.js').read()
SAMPLE = r"""window.__calls=0;window.__in=0;window.__max=0;window.__models=[];window.claude={use:async function(n){ if(n==="db")return window.__mockdb; if(n!=="sample")return null;
 var f=async function(input,opts){window.__calls++;window.__in++;window.__max=Math.max(window.__max,window.__in);window.__models.push(opts.model||"(none)");
   var p=String(input),qs=p.split("=== ATTACHED")[0].split("\n").filter(function(l){return /^\d+\. Round /.test(l)});
   var lines=qs.map(function(l){var m=l.match(/^(\d+)\. Round (\d+): (\S+)/);var sec=p.split("=== "+m[3]+" (")[1]||"";var h=sec.split("\n").filter(function(x){return x.indexOf("# ")===0})[0]||"?";return m[1]+": pong "+m[2]+" "+h});
   await new Promise(function(z){setTimeout(z,400+40*lines.length)});window.__in--;return {text:lines.join("\n"),truncated:false,modelApplied:opts.model||"quick"};}; f.json=null; return f;}};"""
def titles():
    out = []
    for f in sorted(subprocess.check_output(["git", "ls-files", "*.md"], cwd=ROOT, text=True).split()):
        if f.startswith(("tools/browser/explorer/dist/", "docs/ai-cto/rsi/")): continue
        h = [l for l in open(ROOT / f, encoding="utf-8").read().splitlines() if l.startswith("# ")]
        if h: out.append((f, h[0][2:].strip()))
    return out
async def main(BASE):
    q = titles()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"]); ctx = await b.new_context(); await ctx.add_init_script(mock + SAMPLE)
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
        await pg.goto(BASE + "/index.html"); await pg.wait_for_timeout(300)
        asks = [{"n": i + 1, "body": "Round %d: %s (reply 'pong %d' and that file's first line starting with '# ', copied exactly)" % (i + 1, f, i + 1)} for i, (f, _) in enumerate(q)]
        await pg.evaluate("d=>window.__mockdb.doc('mail/F1').set(d)", {"id": "F1", "from": "cloud", "to": "page", "subject": "fleet", "body": "x", "asks": asks, "model": "claude-haiku-5-5", "concurrency": 4, "deadline_ms": 60000, "ts": 1, "sent_at": "x"})
        await pg.wait_for_function("Object.values(window.__store).some(function(v){return v.kind==='shot-result'&&v.re==='F1'})", timeout=90000)
        st = await pg.evaluate("window.__store"); r = [v for v in st.values() if v.get("kind") == "shot-result"][0]
        rep = {x["n"]: x["body"] for v in st.values() if v.get("replies") for x in v["replies"]}
        exact = sum(1 for i, (f, t) in enumerate(q, 1) if rep.get(i) == "pong %d # %s" % (i, t))
        print("%d questions: state %s | exact %d | shot %.1f s | calls %d, max at once %d | models %s | width %s | tier %s"
              % (len(q), r["state"], exact, r["prov"]["ms"] / 1000, await pg.evaluate("window.__calls"), await pg.evaluate("window.__max"),
                 sorted(set(await pg.evaluate("window.__models"))), r["prov"].get("width"), r["prov"]["tier"]))
        print("js errors:", errs or "none"); await b.close()
with served() as BASE:
    asyncio.run(main(BASE))
