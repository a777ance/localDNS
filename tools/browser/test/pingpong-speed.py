import asyncio,sys
from playwright.async_api import async_playwright
mock=open('/home/claude/build/mockdb.js').read()
LAT=int(sys.argv[1]) if len(sys.argv)>1 else 400
# every db round trip costs LAT ms, like the real artifact db
slow="""(function(){var d=window.__mockdb.doc;window.__rt=0;window.__mockdb.doc=function(p){var r=d(p);['get','set','update'].forEach(function(k){var f=r[k];r[k]=async function(x){window.__rt++;await new Promise(function(z){setTimeout(z,%d)});return f.call(r,x)}});return r}})();"""%LAT
SAMPLE=r"""window.__calls=0;window.claude={use:async function(n){ if(n==="db")return window.__mockdb; if(n!=="sample")return null;
 var f=async function(input,opts){window.__calls++;window.__opts=Object.keys(opts);window.__tier=opts.modelTier;var by=function(n){return opts.tools.find(function(t){return t.name===n})};
   var last=input[input.length-1].content;window.__attached=(last.match(/^=== \S+ \(first/gm)||[]).length;
   if(/\[auto-mail\]/.test(last)&&!/STOP HOOK/.test(last)){var re=/--- message (\S+) from[^\n]*\nRound (\d+): (\S+)/g,m,rep=[];while((m=re.exec(last))){
       var sec=last.split("=== "+m[3]+" (first")[1]||"";var h=(sec.split("\n").filter(function(l){return l.indexOf("# ")===0})[0]||"?");rep.push({re:m[1],body:"pong "+m[2]+" "+h})}
     window.__out=await by("mail_reply").execute({replies:rep});
     await new Promise(function(res,rej){var t=setTimeout(res,8000);if(opts.signal)opts.signal.addEventListener("abort",function(){clearTimeout(t);var e=new Error("aborted");e.code="aborted";rej(e)})});}
   var t="**Done.**\n\nA · Replied.\n\nL · Nothing is open.\n\nStopping because: waiting on mail.\n\n**Landed · N = 1:** replied."; if(opts.onText)opts.onText({text:t}); return {text:t,truncated:false};}; f.json=null; return f;}};"""
async def main():
    import json; q=json.load(open('/home/claude/build/pp30.json'))
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":412,"height":900}); await ctx.add_init_script(mock+slow+SAMPLE)
        pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)))
        await pg.route("**/*",lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
        await pg.goto("http://127.0.0.1:8766/index.html"); await pg.wait_for_function("document.getElementById('meta').textContent.includes('files')")
        await pg.wait_for_timeout(300)
        # one burst of 29, written as separate sets (like a 29-op db_write), straight into the store
        await pg.evaluate("q=>{q.forEach(function(x,i){if(i<1)return;var n=i+1;window.__store['mail/r'+n]={id:'r'+n,from:'cloud',to:'page',subject:'round '+n,body:'Round '+n+': '+x.file,sent_at:'x',ts:n}});window.__rt=0;}",q)
        t0=await pg.evaluate("performance.now()")
        await pg.evaluate("window.__mockdb.collection('mail').doc('kick').set({id:'kick',from:'founder',to:'nobody',body:'x',ts:0})")
        await pg.wait_for_function("Object.values(window.__store).filter(function(v){return v.from==='page'}).length>=29",timeout=120000)
        t1=await pg.evaluate("performance.now()")
        st=await pg.evaluate("window.__store")
        ok=sum(1 for v in st.values() if v["from"]=="page" and v["body"]=="pong %s # %s"%(v["re"][1:],q[int(v["re"][1:])-1]["answer"]))
        done=sum(1 for k,v in st.items() if v["from"]=="cloud" and v.get("done_at"))
        await pg.wait_for_function("document.getElementById('go').textContent==='Ask'",timeout=30000); t2=await pg.evaluate("performance.now()")
        print("latency/trip %d ms: 29 answered in %.1f s | exact %d/29 | originals done %d | db round trips %d | turns %d | files attached %d | modelTier %s"%(LAT,(t1-t0)/1000,ok,done,await pg.evaluate("window.__rt"),await pg.evaluate("window.__calls"),await pg.evaluate("window.__attached"),await pg.evaluate("window.__tier")))
        msgs=await pg.inner_text("#msgs"); print("turn ends %.1f s after the replies (stand-in would have spent 8 s writing) | page-written briefing: %s | Stop hook passed: %s | done_at writes: %d"%((t2-t1)/1000,"Answered 29 message(s) from cloud" in msgs,"Stop hook passed" in msgs,done))
        await pg.click("#mailb"); fv=await pg.inner_text("#fv"); print("Mail shows the 29 as done:", fv.count("· done")>=29, "| Mail badge:", await pg.inner_text("#mailb"))
        print("chat bubble short:", len(await pg.inner_text("#msgs"))<3000, "| js errors:", errs or "none")
        await b.close()
asyncio.run(main())
