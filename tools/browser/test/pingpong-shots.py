import asyncio,json
from playwright.async_api import async_playwright
mock=open('/home/claude/build/mockdb.js').read()
slow="""(function(){var d=window.__mockdb.doc;window.__rt=0;window.__mockdb.doc=function(p){var r=d(p);['get','set','update'].forEach(function(k){var f=r[k];r[k]=async function(x){window.__rt++;await new Promise(function(z){setTimeout(z,140)});return f.call(r,x)}});return r}})();"""
# stand-in: two calls at a time; 300 ms per answer line; slips the separator on every 'Round 3' question the first time;
# the jury prompt gets it right; 'fail me' makes the call reject once per page load
SAMPLE=r"""window.__calls=0;window.__slots=2;window.__waitq=[];window.__failed=false;window.claude={use:async function(n){ if(n==="db")return window.__mockdb; if(n!=="sample")return null;
 var f=async function(input,opts){if(window.__slots<=0)await new Promise(function(z){window.__waitq.push(z)});window.__slots--;window.__calls++;
   try{var p=String(input),jury=p.indexOf("YOUR FIRST ANSWERS")>=0,qs=p.split("=== ATTACHED")[0].split("\n").filter(function(l){return /^\d+\. /.test(l)});
   await new Promise(function(z){setTimeout(z,400+300*qs.length)});
   if(/fail me/.test(p)&&!window.__failed){window.__fails=(window.__fails||0)+1;if(window.__fails>=2)window.__failed=true;var e=new Error("x");e.code="rate_limited";throw e}
   var lines=qs.map(function(l){var m=l.match(/^(\d+)\. (.*)$/),t=m[2],r=t.match(/Round (\d+): (\S+)/);
     if(r){var sec=p.split("=== "+r[2]+" (first")[1]||"";var h=sec.split("\n").filter(function(x){return x.indexOf("# ")===0})[0]||"?";return m[1]+": pong "+r[1]+(r[1]==="3"&&!jury?"; ":" ")+h}
     var inp=t.match(/\(input, answer ([\d.]+): ([\s\S]*)\)$/);if(inp)return m[1]+": got "+inp[2].split("\n").length+" line(s) from "+inp[1];
     return m[1]+": ok "+t.slice(0,20)});
   return {text:lines.join("\n"),truncated:false,modelApplied:"stand-in-quick"}}
   finally{window.__slots++;var nx=window.__waitq.shift();if(nx)nx()}}; f.json=null; return f;}};"""
def asks_for(q,lo,hi):return [{"n":i,"body":"Round %d: %s (reply 'pong %d' and that file's first line starting with '# ', copied exactly)"%(i,q[i-1]["file"],i)} for i in range(lo,hi+1)]
async def page(p):
    ctx=await p.new_context(viewport={"width":412,"height":900});await ctx.add_init_script(mock+slow+SAMPLE)
    pg=await ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.route("**/*",lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
    await pg.goto("http://127.0.0.1:8766/index.html");await pg.wait_for_timeout(300);return ctx,pg,errs
async def fire(pg,doc):
    await pg.evaluate("d=>window.__mockdb.doc('mail/'+d.id).set(d)",doc)
    await pg.wait_for_function("id=>Object.values(window.__store).some(function(v){return v.kind==='shot-result'&&v.re===id})",arg=doc["id"],timeout=60000)
    await pg.wait_for_function("document.getElementById('go').textContent==='Ask'",timeout=30000)
    st=await pg.evaluate("window.__store");return st,[v for v in st.values() if v.get("kind")=="shot-result" and v["re"]==doc["id"]][0]
async def main():
    q=json.load(open('/home/claude/build/pp30e.json'))
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx,pg,errs=await page(b)
        # 1. flat shot like run 5, with one planted slip that the jury must fix
        t0=await pg.evaluate("performance.now()");st,r=await fire(pg,{"id":"S1","from":"cloud","to":"page","subject":"flat","body":"x","asks":asks_for(q,1,30),"sent_at":"x","ts":1})
        rep={x["n"]:x for v in st.values() if v.get("re")=="S1" and v.get("replies") for x in v["replies"]}
        ok=sum(1 for n,x in rep.items() if x["body"]=="pong %d # %s"%(n,q[n-1]["answer"]))
        print("1 flat 30: state %s | exact %d/30 | jury fixed %d of %d (answer 3 keeps its first try: %s) | calls %d | waves %d | %.1f s | bundle ids %s"%(r["state"],ok,r["counts"]["jury_fixed"],r["counts"]["jury_asked"],"jury" in rep[3],r["prov"]["calls"],r["counts"]["waves"],r["prov"]["ms"]/1000,sorted(k.split('/')[1] for k,v in st.items() if v.get("re")=="S1" and v.get("replies"))))
        print("  page note:", [l for l in (await pg.inner_text("#msgs")).split("\n") if "Stop hook" in l][-1][:120])
        print("  provenance:",r["prov"]["tier"],"| chars in/out",r["prov"]["chars_in"],r["prov"]["chars_out"])
        # 2. nested shot with a chain: 2 holds two child questions; 3 reads 2's composed answer
        st,r=await fire(pg,{"id":"S2","from":"local","to":"page","subject":"tree","body":"x","asks":[{"n":1,"body":"Round 4: %s (reply 'pong 4' and that file's first line starting with '# ', copied exactly)"%q[3]["file"]},{"n":2,"asks":[{"n":1,"body":"Round 5: %s"%q[4]["file"]},{"n":2,"body":"Round 6: %s"%q[5]["file"]}]},{"n":3,"from":"2","body":"summarise the input"}],"sent_at":"x","ts":2})
        rep={str(x["n"]):x["body"] for v in st.values() if v.get("re")=="S2" and v.get("replies") for x in v["replies"]}
        print("2 tree+chain: state %s | leaves %s | waves %d | parent 2 composed: %s | 3 got: %s"%(r["state"],sorted(rep),r["counts"]["waves"],json.dumps(r["parents"].get("2","")[:60]),rep.get("3")))
        # 3. a dangling chain ends partial with the reason, not a hang
        st,r=await fire(pg,{"id":"S3","from":"cloud","to":"page","subject":"bad ref","body":"x","asks":[{"n":1,"body":"a"},{"n":2,"from":"9","body":"b"}],"sent_at":"x","ts":3})
        print("3 dangling ref: state %s | reason: %s"%(r["state"],r["reason"]))
        # 4. a failing call: first load ends partial; a reload re-fires only what is missing
        doc={"id":"S4","from":"cloud","to":"page","subject":"flaky","body":"x","asks":[{"n":1,"body":"fine one"},{"n":2,"body":"fine two"},{"n":3,"body":"fail me"},{"n":4,"body":"fail me too"}],"sent_at":"x","ts":4}
        await pg.evaluate("window.__failed=false;window.__fails=0")
        st,r=await fire(pg,doc);calls1=await pg.evaluate("window.__calls")
        print("4a first load: state %s | answered %d of 4 | reason: %s"%(r["state"],r["counts"]["answered"],(r["reason"] or "")[:60]))
        store=await pg.evaluate("window.__store");await ctx.close()
        ctx,pg,errs2=await page(b)
        await pg.evaluate("s=>{Object.keys(s).forEach(function(k){window.__store[k]=s[k]});window.__failed=true}",store)
        await pg.evaluate("window.__mockdb.doc('mail/kick').set({id:'kick',from:'founder',to:'x',body:'k',ts:0})")
        await pg.wait_for_function("Object.values(window.__store).some(function(v){return v.kind==='shot-result'&&v.re==='S4'&&v.state==='answered'})",timeout=60000)
        st=await pg.evaluate("window.__store");r=[v for v in st.values() if v.get("kind")=="shot-result" and v["re"]=="S4"][0]
        print("4b after reload: state %s | reused %d | model calls this load %d | duplicate bundles: %s"%(r["state"],r["counts"]["reused"],await pg.evaluate("window.__calls"),len([k for k in st if k.startswith('mail/S4-w1c')])!=len(set(k for k in st if k.startswith('mail/S4-w1c')))))
        print("js errors:", (errs+errs2) or "none")
        await b.close()
asyncio.run(main())
