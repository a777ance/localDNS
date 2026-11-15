import asyncio
from playwright.async_api import async_playwright
mock=open('/home/claude/build/mockdb.js').read()
SAMPLE=r"""window.__calls=0;window.claude={use:async function(n){ if(n==="db")return window.__mockdb; if(n!=="sample")return null;
 var f=async function(input,opts){window.__calls++;var by=function(n){return opts.tools.find(function(t){return t.name===n})};
   var last=input[input.length-1].content;
   if(/\[auto-mail\]/.test(last)&&!/STOP HOOK/.test(last)){var re=/--- message (\S+) from[^\n]*\nRound (\d+)/g,m,rep=[];while((m=re.exec(last)))rep.push({re:m[1],body:"pong "+m[2]});
     window.__out=await by("mail_reply").execute({replies:rep});}
   var t="**Done.** Answered.\n\nStopping because: waiting on mail.\n\n**Landed · N = 1:** replied."; if(opts.onText)opts.onText({text:t}); return {text:t,truncated:false};}; f.json=null; return f;}};"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":1200,"height":900}); await ctx.add_init_script(mock+SAMPLE)
        # 28 messages already waiting before the page opens
        pre="".join("window.__mockdb.doc('mail/m%02d').set({id:'m%02d',from:'cloud',to:'page',subject:'round %d/30',body:'Round %d: README.md',sent_at:'x',ts:%d});"%(i,i,i,i,i) for i in range(3,31))
        await ctx.add_init_script("window.addEventListener('DOMContentLoaded',function(){"+pre+"})")
        pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)))
        await pg.route("**/*",lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort())
        await pg.goto("http://127.0.0.1:8766/index.html")
        await pg.wait_for_function("Object.values(window.__store).filter(function(v){return v.from==='page'}).length>=28",timeout=60000)
        st=await pg.evaluate("window.__store")
        pongs=[v for v in st.values() if v["from"]=="page"]
        print("replies:",len(pongs),"| all re ok:",all(st["mail/"+v["re"]]["body"].split()[1].rstrip(":")==v["body"].split()[1] for v in pongs),"| originals done:",sum(1 for k,v in st.items() if v["from"]=="cloud" and v.get("done_at")))
        print("model calls (turns):",await pg.evaluate("window.__calls"),"| js errors:",errs or "none")
        await b.close()
asyncio.run(main())
