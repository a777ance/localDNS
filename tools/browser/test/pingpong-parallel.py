import asyncio,sys,json
from playwright.async_api import async_playwright
mock=open('/home/claude/build/mockdb.js').read()
LAT=140
slow="""(function(){var d=window.__mockdb.doc;window.__rt=0;window.__mockdb.doc=function(p){var r=d(p);['get','set','update'].forEach(function(k){var f=r[k];r[k]=async function(x){window.__rt++;await new Promise(function(z){setTimeout(z,%d)});return f.call(r,x)}});return r}})();"""%LAT
# stand-in model: 400 ms to start, 300 ms per answer line it writes (output time dominates), answers from the attached text only
SAMPLE=r"""window.__calls=0;window.__inflight=0;window.__maxin=0;window.claude={use:async function(n){ if(n==="db")return window.__mockdb; if(n!=="sample")return null;
 var f=async function(input,opts){window.__calls++;window.__inflight++;window.__maxin=Math.max(window.__maxin,window.__inflight);window.__tier=opts&&opts.modelTier;window.__plen=Math.max(window.__plen||0,String(input).length);
   var p=String(input),qs=[],re=/^(\d+)\. Round (\d+): (\S+)/gm,m;while((m=re.exec(p)))qs.push(m);
   await new Promise(function(z){setTimeout(z,400+300*qs.length)});
   var lines=qs.map(function(m){var sec=p.split("=== "+m[3]+" (first")[1]||"";var h=sec.split("\n").filter(function(l){return l.indexOf("# ")===0})[0]||"?";return m[1]+": pong "+m[2]+" "+h});
   window.__inflight--;return {text:lines.join("\n"),truncated:false};}; f.json=null; return f;}};"""
async def main():
    q=json.load(open('/home/claude/build/pp30c.json'))
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":412,"height":900}); await ctx.add_init_script(mock+slow+SAMPLE)
        pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)))
        await pg.route("**/*",lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
        await pg.goto("http://127.0.0.1:8766/index.html"); await pg.wait_for_function("document.getElementById('meta').textContent.includes('files')"); await pg.wait_for_timeout(500)
        asks=[{"n":i+1,"body":"Round %d: %s (reply 'pong %d' and that file's first line starting with '# ', copied exactly)"%(i+1,x["file"],i+1)} for i,x in enumerate(q)]
        t0=await pg.evaluate("performance.now()")
        await pg.evaluate("a=>window.__mockdb.doc('mail/AQ').set({id:'AQ',from:'cloud',to:'page',subject:'run 4',body:'30 questions in asks',asks:a,sent_at:'x',ts:1})",asks)
        await pg.wait_for_function("document.getElementById('go').textContent==='Ask'&&Object.values(window.__store).some(function(v){return v.from==='page'})",timeout=60000)
        await pg.wait_for_function("document.getElementById('go').textContent==='Ask'",timeout=60000)
        t1=await pg.evaluate("performance.now()")
        st=await pg.evaluate("window.__store")
        rep=[r for v in st.values() if v["from"]=="page" and v.get("replies") for r in v["replies"]]
        ok=sum(1 for r in rep if r["body"]=="pong %d # %s"%(r["n"],q[r["n"]-1]["answer"]))
        print("30 questions in one doc: answered %d, exact %d/30, end to end %.1f s | bundles %d | db trips %d | model calls %d, max at once %d | tier %s | longest prompt %d chars"%(len(rep),ok,(t1-t0)/1000,sum(1 for v in st.values() if v['from']=='page'),await pg.evaluate("window.__rt"),await pg.evaluate("window.__calls"),await pg.evaluate("window.__maxin"),await pg.evaluate("window.__tier"),await pg.evaluate("window.__plen")))
        msgs=await pg.inner_text("#msgs"); print("page briefing Done:", "**Done" in msgs or "Done." in msgs, "| Stop hook passed:", "Stop hook passed" in msgs)
        await pg.click("#mailb"); fv=await pg.inner_text("#fv"); print("ask doc shows done:", "run 4" in fv and "· done" in fv, "| badge:", await pg.inner_text("#mailb"))
        # a plain single message still works through the same path
        await pg.evaluate("window.__mockdb.doc('mail/P1').set({id:'P1',from:'local',to:'page',subject:'one',body:'Round 7: '+%s,sent_at:'x',ts:2})"%json.dumps(q[6]["file"]))
        await pg.wait_for_function("Object.values(window.__store).some(function(v){return v.from==='page'&&v.re==='P1'})",timeout=30000)
        r=[v for v in (await pg.evaluate("window.__store")).values() if v.get("re")=="P1"][0]
        print("single message from local answered:", r["to"]=="local", "|", r["replies"][0]["body"][:40])
        print("js errors:", errs or "none"); await b.close()
asyncio.run(main())
