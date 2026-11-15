"""Throughput: one shot of every doc title, a named model, four calls at once (the haiku superfleet)."""
import asyncio, sys, pathlib, json, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _serve import served, CHROME, HERE
from playwright.async_api import async_playwright
ROOT = HERE.parents[2]
mock = open(HERE / 'mockdb.js').read()
SAMPLE = r"""window.__calls=0;window.__in=0;window.__max=0;window.__models=[];window.claude={use:async function(n){ if(n==="db")return window.__mockdb; if(n!=="sample")return null;
 var f=async function(input,opts){window.__calls++;window.__in++;window.__max=Math.max(window.__max,window.__in);window.__models.push(opts.model||"(none)");
   if(String(input).indexOf("numbered slices")>0){var parts=String(input).split(/\n?=== slice (\d+) · [^\n]* ===\n/),ls=[];for(var i=1;i<parts.length;i+=2){var mm=parts[i+1].replace(/\n=== end of slices ===$/,"").match(/DEC-\d{3}/);if(mm)ls.push(parts[i]+": "+mm[0])}
     await new Promise(function(z){setTimeout(z,300)});window.__in--;return {text:ls.join("\n")+"\nEND",truncated:false,modelApplied:opts.model||"quick"};}
   var p=String(input),qs=p.split("=== ATTACHED")[0].split("\n").filter(function(l){return /^\d+\. Round /.test(l)});
   var lines=qs.map(function(l){var m=l.match(/^(\d+)\. Round (\d+): (\S+)/);var sec=p.split("=== "+m[3]+" (")[1]||"";var h=sec.split("\n").filter(function(x){return x.indexOf("# ")===0})[0]||"?";return / title$/.test(l)?m[1]+": "+h.slice(2).trim():m[1]+": pong "+m[2]+" "+h});
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
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: None if "lane mode" in str(e) else errs.append(str(e)))
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
        # fleet shot: the page expands 1000 asks itself, 250 answers a call, 2 lanes as a pipeline, no tools, page-side check
        await pg.evaluate("window.__calls=0;window.__max=0")
        await pg.evaluate("d=>window.__mockdb.doc('mail/F2').set(d)", {"id": "F2", "from": "cloud", "to": "page", "subject": "fleet2", "body": "x", "model": "claude-haiku-5-5", "concurrency": 2,
            "per_call": 250, "attach_max": 600, "tools": False, "jury": False, "deadline_ms": 120000,
            "fleet": {"match": "\\.md$", "ask": "Round 0: {file} title", "count": 1000, "check": "first_heading"}, "sent_at": "2026-11-15T21:00:00Z", "ts": 2})
        await pg.wait_for_function("Object.values(window.__store).some(function(v){return v.kind==='shot-result'&&v.re==='F2'})", timeout=120000)
        st = await pg.evaluate("window.__store"); r2 = [v for v in st.values() if v.get("kind") == "shot-result" and v["re"] == "F2"][0]
        print("fleet 1000: state %s | answered %d | check %s | calls %d, max at once %d | files %s"
              % (r2["state"], r2["counts"]["answered"], {k: r2["check"][k] for k in ("exact", "missed")}, await pg.evaluate("window.__calls"), await pg.evaluate("window.__max"), r2["check"]["files"]))
        # slice shot: 1000 shards of 1000 characters, sparse answers, graded by the page against a regex
        await pg.evaluate("window.__calls=0;window.__max=0")
        await pg.evaluate("d=>window.__mockdb.doc('mail/F3').set(d)", {"id": "F3", "from": "cloud", "to": "page", "subject": "slices", "body": "x", "model": "claude-haiku-5-5", "concurrency": 2,
            "per_call": 125, "tools": False, "jury": False, "deadline_ms": 120000,
            "fleet": {"slice": 1000, "ask": "copy the first decision id", "count": 1000, "sparse": True, "check": {"first_match": "DEC-\\d{3}"}}, "sent_at": "2026-11-15T22:00:00Z", "ts": 3})
        await pg.wait_for_function("Object.values(window.__store).some(function(v){return v.kind==='shot-result'&&v.re==='F3'})", timeout=120000)
        st = await pg.evaluate("window.__store"); r3 = [v for v in st.values() if v.get("kind") == "shot-result" and v["re"] == "F3"][0]
        print("slices 1000: state %s | answered %d | check %s | calls %d, max at once %d | sha %s"
              % (r3["state"], r3["counts"]["answered"], {k: r3["check"][k] for k in ("slices", "slice_chars", "expected_hits", "exact", "missed")}, await pg.evaluate("window.__calls"), await pg.evaluate("window.__max"), r3["check"]["expected_sha256"][:16]))
        # frame probe: two lane frames of this same page, two calls each
        await pg.evaluate("d=>window.__mockdb.doc('mail/F4').set(d)", {"id": "F4", "from": "cloud", "to": "page", "subject": "frames", "body": "x", "model": "claude-haiku-5-5", "probe": {"frames": 2, "each": 2}, "sent_at": "2026-11-15T22:10:00Z", "ts": 4})
        await pg.wait_for_function("Object.values(window.__store).some(function(v){return v.kind==='shot-result'&&v.re==='F4'})", timeout=60000)
        st = await pg.evaluate("window.__store"); r4 = [v for v in st.values() if v.get("kind") == "shot-result" and v["re"] == "F4"][0]
        print("frame probe: state %s | ready %s | calls %s" % (r4["state"], r4["check"]["ready"], [(c["frame"], c["call"], c["error"]) for c in r4["check"]["calls"]]))
        print("js errors:", errs or "none"); await b.close()
with served() as BASE:
    asyncio.run(main(BASE))
