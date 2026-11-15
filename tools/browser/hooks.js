/* hooks.js: JavaScript ports of the repo's Claude Code hooks, for a place with no Python and no shell
 * (the artifact page). Each port keeps the Python original's rules and message text; tests/parity.js runs the same
 * inputs through the original and the port and compares them. The Python original stays the source of truth.
 *
 *   decide-act.py (Stop)         full port: LEAD ACT CD REHEARSE HEDGE TILE L NEXT LANDING.
 *                                SCRATCH is omitted on purpose: there is no scratchpad directory in the browser.
 *   cardinal.py   (PreToolUse)   full port, state kept in an in-memory overlay on the repo snapshot.
 *   timing.py     (PostToolUse)  full port.
 *   refeed.sh     (SessionStart) context text is read from the .sh heredoc at run time; the sync half reports the snapshot.
 *   momentum.sh   (Stop)         full port (inert unless .claude/.momentum-on exists, which nothing here creates).
 *   gate.sh       (PreToolUse Bash)  fails closed on `git commit`: the static checks cannot run here.
 *
 * Known, deliberate differences from Python's re: \d \b \s are the JS ones (ASCII-leaning); \W in the Decide / Act / L
 * headings is made Unicode-aware to match; a bare \r in a reply is not treated as a line break by Python's ^ and $ but is by JS's.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.OodaHooks = factory();
})(this, function () {
  "use strict";

  /* ------------------------------------------------------------ runtime tracer (off unless create({trace:true})) */
  // Records what a hook does while it runs: each function it calls (named after the Python function it ports),
  // the arguments and return value, each repo file it reads, writes or checks, and each Briefing rule decision.
  var TR = null; // the active step list for the hook being run, or null when tracing is off
  function brief(v) {
    if (v === undefined) return "undefined";
    if (v && typeof v === "object" && typeof v.read === "function") return "<repo>";
    if (v && typeof v === "object" && v.vfs && "payload" in v) { var o = {}; Object.keys(v).forEach(function (k) { if (k !== "vfs" && k !== "now") o[k] = v[k]; }); v = o; }
    var t; try { t = typeof v === "string" ? JSON.stringify(v) : JSON.stringify(v); } catch (e) { t = String(v); }
    if (t === undefined) t = String(v);
    return t.length > 240 ? t.slice(0, 240) + "…(" + t.length + " chars)" : t;
  }
  var DEPTH = 0;
  function step(kind, what, detail) { if (TR) TR.push({ d: DEPTH, k: kind, w: what, x: detail === undefined ? "" : detail, t: (typeof performance !== "undefined" ? performance.now() : Date.now()) }); }
  function traced(file, name, fn) {
    return function () {
      if (!TR) return fn.apply(this, arguments);
      var args = Array.prototype.map.call(arguments, brief).join(", "), t0 = (typeof performance !== "undefined" ? performance.now() : Date.now());
      step("call", file + " › " + name, "(" + args + ")"); DEPTH++;
      try { var r = fn.apply(this, arguments); DEPTH--; step("return", file + " › " + name, brief(r) + "  [" + ((typeof performance !== "undefined" ? performance.now() : Date.now()) - t0).toFixed(2) + " ms]"); return r; }
      catch (e) { DEPTH--; step("raise", file + " › " + name, (e && e.name) + ": " + (e && e.message)); throw e; }
    };
  }

  /* ------------------------------------------------------------ helpers that make JS behave like the Python code */
  function splitlines(t) {
    var parts = t.split(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/);
    if (parts.length && parts[parts.length - 1] === "") parts.pop();
    return parts;
  }
  function cut(s, n) { return Array.from(s).slice(0, n).join(""); }
  function pyrepr(s) {
    var q = (s.indexOf("'") >= 0 && s.indexOf('"') < 0) ? '"' : "'", out = q;
    for (var ch of s) {
      var c = ch.codePointAt(0);
      if (ch === q || ch === "\\") out += "\\" + ch;
      else if (ch === "\n") out += "\\n";
      else if (ch === "\r") out += "\\r";
      else if (ch === "\t") out += "\\t";
      else if (ch !== " " && /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]/u.test(ch)) {
        out += c < 0x100 ? "\\x" + c.toString(16).padStart(2, "0") : c < 0x10000 ? "\\u" + c.toString(16).padStart(4, "0") : "\\U" + c.toString(16).padStart(8, "0");
      } else out += ch;
    }
    return out + q;
  }
  function sha256hex(str) { // small synchronous SHA-256 (only used when .claude/.matrix-rehearsed exists)
    var K = [], H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19], i, j;
    (function () { var p = 2, n = 0; while (n < 64) { var ok = true; for (var d = 2; d * d <= p; d++) if (p % d === 0) { ok = false; break; } if (ok) { K[n++] = (Math.pow(p, 1 / 3) % 1) * 4294967296 | 0; } p++; } })();
    var bytes = Array.from(new TextEncoder().encode(str)), l = bytes.length * 8;
    bytes.push(0x80); while (bytes.length % 64 !== 56) bytes.push(0);
    for (i = 7; i >= 0; i--) bytes.push(i >= 4 ? 0 : (l >>> (i * 8)) & 255);
    var rr = function (x, n) { return (x >>> n) | (x << (32 - n)); };
    for (var off = 0; off < bytes.length; off += 64) {
      var w = [];
      for (i = 0; i < 16; i++) w[i] = (bytes[off + 4 * i] << 24) | (bytes[off + 4 * i + 1] << 16) | (bytes[off + 4 * i + 2] << 8) | bytes[off + 4 * i + 3];
      for (i = 16; i < 64; i++) { var s0 = rr(w[i - 15], 7) ^ rr(w[i - 15], 18) ^ (w[i - 15] >>> 3), s1 = rr(w[i - 2], 17) ^ rr(w[i - 2], 19) ^ (w[i - 2] >>> 10); w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0; }
      var a = H.slice();
      for (i = 0; i < 64; i++) {
        var S1 = rr(a[4], 6) ^ rr(a[4], 11) ^ rr(a[4], 25), ch = (a[4] & a[5]) ^ (~a[4] & a[6]), t1 = (a[7] + S1 + ch + K[i] + w[i]) | 0;
        var S0 = rr(a[0], 2) ^ rr(a[0], 13) ^ rr(a[0], 22), mj = (a[0] & a[1]) ^ (a[0] & a[2]) ^ (a[1] & a[2]), t2 = (S0 + mj) | 0;
        a = [(t1 + t2) | 0, a[0], a[1], a[2], (a[3] + t1) | 0, a[4], a[5], a[6]];
      }
      for (j = 0; j < 8; j++) H[j] = (H[j] + a[j]) | 0;
    }
    return H.map(function (x) { return ("00000000" + (x >>> 0).toString(16)).slice(-8); }).join("");
  }

  /* ------------------------------------------------------------ the repo snapshot with an in-memory overlay (the "disk") */
  function makeVfs(files, nowFn) {
    var over = {}, gone = {};
    function dirHas(dir) { var pre = dir.replace(/\/+$/, "") + "/", k; for (k in over) if (over[k] && k.indexOf(pre) === 0) return true; for (k in files) if (!gone[k] && k.indexOf(pre) === 0) return true; return false; }
    return {
      exists: function (p) { var r = !!over[p] || (!gone[p] && ((p in files) || dirHas(p))); step("file", "exists " + p, r ? "yes" : "no"); return r; },
      read: function (p) { if (over[p]) { step("file", "read " + p, over[p].t.length + " chars (session state)"); return over[p].t; } if (!gone[p] && p in files) { step("file", "read " + p, files[p].length + " chars (repo snapshot)"); return files[p]; } step("file", "read " + p, "not found"); var e = new Error("ENOENT " + p); e.code = "ENOENT"; throw e; },
      write: function (p, t) { step("file", "write " + p, brief(t)); over[p] = { t: t, m: nowFn() }; delete gone[p]; },
      append: function (p, t) { var cur = ""; try { cur = this.read(p); } catch (e) { } this.write(p, cur + t); },
      unlink: function (p) { step("file", "delete " + p); delete over[p]; if (p in files) gone[p] = true; },
      mtime: function (p) { return over[p] ? over[p].m : 0; },
      list: function (dir) { var _r = this._list(dir); step("file", "list " + dir, _r.length + " entries"); return _r; },
      _list: function (dir) { var pre = dir.replace(/\/+$/, "") + "/", seen = {}, k, rest; for (k in files) if (!gone[k] && k.indexOf(pre) === 0) { rest = k.slice(pre.length); if (rest.indexOf("/") < 0) seen[rest] = 1; } for (k in over) if (over[k] && k.indexOf(pre) === 0) { rest = k.slice(pre.length); if (rest.indexOf("/") < 0) seen[rest] = 1; } return Object.keys(seen).sort(); }
    };
  }

  /* ------------------------------------------------------------ Stop: decide-act.py */
  var HEDGES = ["should work", "probably works", "probably work", "may have worked", "might have worked", "should be fine"];
  var RE_DECIDE = /^[^\p{L}\p{N}_]*(?:Decide[ds]?\b|D · )[^\n]*$/mu; // DEBT-014: the letter form counts too
  var RE_ACT = /^[^\p{L}\p{N}_]*(?:Act(?:ed)?\b|A · )[^\n]*$/mu;
  var RE_STEP_LETTER = /^[^\p{L}\p{N}_]*(?:O|OO|D|A|L) · /u;

  function lastAssistantText(records) {
    var text = "";
    records.forEach(function (rec) {
      var msg = rec.message !== undefined ? rec.message : rec;
      if (msg.role !== "assistant" && rec.type !== "assistant") return;
      var content = msg.content === undefined ? "" : msg.content, parts;
      if (typeof content === "string") parts = [content];
      else parts = content.filter(function (b) { return b && typeof b === "object" && b.type === "text"; }).map(function (b) { return b.text === undefined ? "" : b.text; });
      var joined = parts.filter(function (p) { return p; }).join("\n");
      if (joined) text = joined;
    });
    return text;
  }
  function decideItems(text) {
    var m = RE_DECIDE.exec(text);
    if (!m) return [];
    var items = [], started = false, lines = splitlines(text.slice(m.index + m[0].length));
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (/^\s*\d+\.\s+\S/.test(line)) { items.push(line.trim()); started = true; }
      else if (started && line.trim() === "") break;
      else if (started && !/^\s*\d+\./.test(line)) break;
    }
    return items;
  }
  function actLines(text) {
    var d = RE_DECIDE.exec(text);
    if (!d) return 0;
    var dEnd = d.index + d[0].length, tail = text.slice(dEnd);
    var m = RE_ACT.exec(tail);
    if (!m) return 0;
    var n = 0, lines = splitlines(text.slice(dEnd + m.index + m[0].length));
    for (var i = 0; i < lines.length; i++) {
      if (/^#{1,3}\s|^\*\*[A-Z]\w+\.?\*\*\.?\s*$/.test(lines[i]) || RE_STEP_LETTER.test(lines[i])) break;
      if (/^\s*(\d+\.|[-*])\s+\S/.test(lines[i])) n++;
    }
    return n;
  }
  function prose(text) {
    text = text.replace(/```[\s\S]*?```/g, "");
    text = text.replace(/`[^`\n]*`/g, "");
    return text.replace(/["\u201c][^"\u201d\n]*["\u201d]/g, "");
  }
  function loopItems(text) {
    var m = /^[^\p{L}\p{N}_]*L · [^\n]*$/mu.exec(text);
    if (!m) return [];
    var items = [], lines = splitlines(text.slice(m.index + m[0].length));
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (/^#{1,3}\s|^\*\*Landed|^Stopping because:/.test(line)) break;
      if (/^\s*(\d+\.|[-*])\s+\S/.test(line) && !/DEC-\d{3}|sub-loop running/.test(line)) items.push(cut(line.trim(), 160));
    }
    return items;
  }
  function nextAction(vfs) {
    // `git status --porcelain` is empty for the snapshot: it is a clean checkout, so there is nothing "changed and not shipped".
    if (vfs.list(".claude/.matrix-stalls").some(function (n) { return /\.json$/.test(n); }))
      return "a Matrix stall is open. Diagnose it: python3 tools/matrix.py orient.stall";
    var names = ["docs/ai-cto/superqueue.md", "docs/ai-cto/handoff.md"];
    for (var i = 0; i < names.length; i++) {
      var queue;
      try { queue = vfs.read(names[i]); } catch (e) { continue; }
      var re = /^- \*\*(S?Q-\d{3}) · ([^\n]*?)\*\*[^\n]*$/gm, m;
      while ((m = re.exec(queue)) !== null) {
        if (!/BLOCKED|DONE|SKIPPED/.test(m[0])) return "the next queue item is " + m[1] + " · " + cut(m[2], 90) + " (" + names[i] + "). Start it now.";
      }
      return null;
    }
    return null;
  }
  function ruleMarks(reasons) {
    // Trace only. A rule that looked and found nothing is "pass"; a rule that never looked is "not checked",
    // with the reason, so the trace never claims a check that did not run.
    var cur = null, at = 0, skip = null;
    function close() {
      if (!cur || !TR) return;
      step("rule", cur, reasons.length > at ? "FIRED: " + brief(reasons[reasons.length - 1].split("\n")[0]) : skip ? "not checked: " + skip : "pass");
    }
    var f = function (name) { close(); cur = name; at = reasons.length; skip = null; };
    f.skip = function (why) { skip = why; };
    f.done = close; return f;
  }
  function review(text, vfs) {
    var reasons = [], i;
    var RM = ruleMarks(reasons);
    // SCRATCH is omitted: no scratchpad directory exists in the browser.
    RM("LEAD");
    var first = splitlines(text).filter(function (l) { return l.trim(); })[0] || "";
    if (!/^\*\*(Done|Partial|Blocked|Waiting)[.:,]?\*\*[.:,]?(\s|$)/.test(first.trim()))
      reasons.push("BRIEFING LEAD: the reply must open with one bold state word (**Done**, **Partial**, **Blocked**, or **Waiting**). It opened with: " + pyrepr(cut(first.trim(), 80)) + ". Restate the reply with the state word first.");
    RM("ACT");
    var items = decideItems(text), acted = items.length ? actLines(text) : 0;
    if (!items.length) RM.skip("no numbered list under a Decide step (the word or 'D · ')");
    if (items.length && acted < items.length)
      reasons.push("OODA ACT: the Decide list has " + items.length + " numbered item(s) and the Act section reports " + acted + ". Act on them now, in order, without choosing between them or asking first, and report one Act line per item (or say why that item is blocked). Skip only an item the user has marked punt. Irreversible or outward-facing actions still need a confirm first.\n\n" + items.join("\n"));
    RM("CD");
    var blocks = [], bre = /```bash\n([\s\S]*?)```/g, bm;
    while ((bm = bre.exec(text)) !== null) blocks.push(bm[1]);
    if (!blocks.length) RM.skip("no bash block in the reply");
    for (i = 0; i < blocks.length; i++) {
      var lines = splitlines(blocks[i]).map(function (l) { return l.trim(); }).filter(function (l) { return l && l.indexOf("#") !== 0; });
      if (lines.length && lines[0].indexOf("cd /home/user/") === 0) { reasons.push("COMMAND CD: this bash block uses the cloud container's path (/home/user/...), which does not exist on the founder's machine. Use: cd ~/localDNS"); break; }
      if (lines.length && lines[0].indexOf("cd ") !== 0) { reasons.push("COMMAND CD: every bash block must start with the cd to the repo. This block starts with: " + pyrepr(cut(lines[0], 80))); break; }
    }
    RM("REHEARSE");
    if (!blocks.length) RM.skip("no bash block in the reply");
    else if (text.indexOf("Not rehearsed:") >= 0) {
      var nr = splitlines(text).filter(function (l) { return l.indexOf("Not rehearsed:") >= 0; })[0] || "";
      RM.skip("a 'Not rehearsed:' line exempts every bash block in the reply (" + blocks.length + " exempted: " +
        blocks.map(function (b) { return pyrepr(cut(splitlines(b).filter(function (l) { return l.trim() && l.trim().indexOf("#") !== 0; }).slice(0, 2).join(" ; "), 60)); }).join(", ") +
        "). The line: " + pyrepr(cut(nr.trim(), 140)));
    }
    if (text.indexOf("Not rehearsed:") < 0) {
      var done = {};
      try { splitlines(vfs.read(".claude/.matrix-rehearsed")).forEach(function (l) { var p = l.split("\t"); if (p[1] === "0") done[p[0]] = 1; }); } catch (e) { }
      for (i = 0; i < blocks.length; i++) {
        var ls = splitlines(blocks[i].trim()).map(function (l) { return l.trim(); }).filter(function (l) { return l && l.indexOf("#") !== 0; });
        if (ls.length && /^cd\s+\S+$/.test(ls[0])) ls = ls.slice(1);
        else if (ls.length) ls[0] = ls[0].replace(/^cd\s+\S+\s*&&\s*/, "");
        var body = ls.join("\n");
        if (body && !done[sha256hex(body)]) {
          reasons.push("REHEARSE: this command is being handed to the founder without having been run: " + pyrepr(cut(body, 100)) + ". Run it first in a copy of his checkout: python3 tools/matrix.py decide.rehearse [--at REV] [--setup CMD] \"COMMAND\" (it must exit 0). If it cannot be rehearsed here, say so in the reply on a line starting 'Not rehearsed:' with the reason.");
          break;
        }
      }
    }
    RM("HEDGE");
    var low = prose(text).toLowerCase(), found = HEDGES.filter(function (h) { return low.indexOf(h) >= 0; });
    if (found.length) reasons.push("NO HEDGE: the reply says " + found.map(pyrepr).join(", ") + ". Replace it with the check that would confirm it, or with what was verified.");
    RM("TILE");
    var log = null;
    try { log = vfs.read("docs/ai-cto/blocked.md"); } catch (e) { }
    var decs = [], dre = /DECISION · (DEC-\d{3})/g, dm;
    while ((dm = dre.exec(text)) !== null) if (decs.indexOf(dm[1]) < 0) decs.push(dm[1]);
    if (!decs.length) RM.skip("no 'DECISION · DEC-NNN' tile in the reply");
    decs.forEach(function (dec) {
      var missing = ["Action if GO:", "Action if NO GO:", "Decision needed:"].filter(function (p) { return text.indexOf(p) < 0; });
      if (log !== null && log.indexOf("**" + dec + " ") < 0) missing.push("an entry for " + dec + " in docs/ai-cto/blocked.md");
      if (missing.length) reasons.push("TILE: the tile for " + dec + " is missing: " + missing.join("; ") + ".");
    });
    RM("L STEP");
    if (/^#{1,3}\s*(Still open|Not yet|What is (still )?(not|left)|Open items|Limits)\b/mi.test(text))
      reasons.push("L STEP: what is left open belongs under one heading that starts 'L · ', not under a heading of its own wording. Each L item either cites the founder's DEC id or is the loop's.");
    RM("L ITEMS");
    var mine = loopItems(text);
    if (!/^[^\p{L}\p{N}_]*L · /mu.test(text)) RM.skip("no 'L · ' step in the reply");
    if (mine.length)
      reasons.push("L ITEMS OPEN: " + mine.length + " item(s) under L are the loop's own (no DEC id). Do not stop. Start a sub-OODA loop for each one now, in parallel where they do not touch the same files: one Agent call per item in a single message (isolation: worktree), each told to observe, orient, decide, act on its item, land it by pull request into leader, and report. An item only the founder can close becomes a DEC tile and leaves L.\n\n" + mine.join("\n"));
    RM("L DECS");
    var lmm = /^[^\p{L}\p{N}_]*L · [^\n]*$/mu.exec(text);
    if (!lmm) RM.skip("no 'L · ' step in the reply");
    else if (log === null) RM.skip("docs/ai-cto/blocked.md could not be read");
    if (lmm && log !== null) {
      var openDecs = {}, om, ore = /\*\*(DEC-\d{3}) · [^\n]*· OPEN\*\*/g;
      while ((om = ore.exec(log)) !== null) openDecs[om[1]] = 1;
      var lEndRel = /^(#{1,3}\s|\*\*Landed|Stopping because:|For a Claude Code session:)/m.exec(text.slice(lmm.index + lmm[0].length));
      var lEnd = lEndRel ? lmm.index + lmm[0].length + lEndRel.index : text.length;
      var ids = function (s) { return s.match(/DEC-\d{3}/g) || []; };
      var inL = {}; ids(text.slice(lmm.index, lEnd)).forEach(function (x) { inL[x] = 1; });
      var tileIds = {}, tm, tre = /DECISION · (DEC-\d{3})/g; while ((tm = tre.exec(text)) !== null) tileIds[tm[1]] = 1;
      var named = {}; ids(text.slice(0, lmm.index) + text.slice(lEnd)).forEach(function (x) { named[x] = 1; });
      var missing = Object.keys(named).filter(function (x) { return openDecs[x] && !inL[x] && !tileIds[x]; }).sort().reverse();
      if (missing.length) reasons.push("L DECS: the reply names open founder decision(s) " + missing.join(", ") + " outside the L step. Nothing open is reported under any other heading: list each under 'L · ' with its DEC id.");
    }
    RM("NEXT");
    if (text.indexOf("Stopping because:") >= 0) RM.skip("a 'Stopping because:' line ends the turn, so the queue on disk was not consulted");
    if (text.indexOf("Stopping because:") < 0) {
      var todo = null;
      try { todo = nextAction(vfs); } catch (e) { todo = null; }
      if (todo) reasons.push("NEXT ACTION: do not stop here; " + todo + " If stopping is right (waiting on the founder, on an event, or the work was a question and not a task), say so on a line starting 'Stopping because:' and end the reply.");
    }
    RM("LANDING");
    var last = splitlines(text).filter(function (l) { return l.trim(); }).pop() || "";
    if (!/^\*\*Landed · N = \d+:\*\*\s+\S/.test(last.trim()))
      reasons.push("LANDING: the reply must end with one line that says where we landed, in this form: **Landed · N = <count>:** then where each of the N items in play stands, in one sentence. It ended with: " + pyrepr(cut(last.trim(), 80)));
    RM.done();
    return reasons;
  }
  function hookDecideAct(c) {
    var data = c.payload;
    if (data.stop_hook_active) return { code: 0, stdout: "", stderr: "" };
    var reasons;
    try {
      var records = c.transcript || data.transcript_records || [];
      var text = lastAssistantText(records);
      reasons = text.trim() ? review(text, c.vfs) : [];
    } catch (e) { return { code: 0, stdout: "", stderr: "" }; } // fail open, like the original
    if (!reasons.length) return { code: 0, stdout: "", stderr: "" };
    return { code: 0, stdout: JSON.stringify({ decision: "block", reason: reasons.join("\n\n") }), stderr: "" };
  }

  lastAssistantText = traced("decide-act.py", "last_assistant_text", lastAssistantText);
  decideItems = traced("decide-act.py", "decide_items", decideItems);
  actLines = traced("decide-act.py", "act_lines", actLines);
  prose = traced("decide-act.py", "prose", prose);
  loopItems = traced("decide-act.py", "loop_items", loopItems);
  nextAction = traced("decide-act.py", "next_action", nextAction);
  review = traced("decide-act.py", "review", review);
  hookDecideAct = traced("decide-act.py", "main", hookDecideAct);

  /* ------------------------------------------------------------ PreToolUse: cardinal.py */
  var HARD_BASH = /\brm\s+-[a-zA-Z]*[rR]|\brm\s+--recursive|\bgit\s+push\b[^\n]*--force(?!-with-lease)|\bgit\s+push\b[^\n]*\s-f\b|\bgit\s+reset\s+--hard\b|\bgit\s+clean\b[^\n]*-[a-zA-Z]*f|\bmkfs(\.|\s)|\bdd\s+if=|\bshutdown\b|\breboot\b|\bdocker\s+(system\s+prune|rm\s+-f)/;
  var FILE_VERB = /(?:^|[;&|(]\s*|\$\(\s*|`\s*)(cat|head|tail|less|more|bat|nl|tac|strings|xxd|od|hexdump|awk|sed|tee|cp|mv|install|touch|truncate|chmod|chown|grep|rg|find|ls|tree|stat|wc|diff|cmp)\b/;
  var ROUTED_FILE_METHOD = /tools\/matrix\.py\s+(observe\.(read|find|search)|act\.(write|edit)|observe\.probe\s+path)\b/;
  var HARD_POLL_TOOLS = ["ReadNotifications", "mcp__github__pull_request_read", "mcp__github__get_check_run", "mcp__github__actions_get", "mcp__github__actions_list", "mcp__claude-code-remote__list_events", "mcp__claude-code-remote__get_event"];
  var READ_ONLY = /^\s*(ls|cat|head|tail|grep|rg|find|wc|diff|stat|file|which|command|echo|printf|sort|uniq|cut|tr|test|true|pwd|date|env|git\s+(status|log|diff|show|branch|fetch|remote|rev-parse)|python3?\s+tools\/check-)\b/;

  function stripQuoted(cmd) {
    cmd = cmd.replace(/<<-?\s*(['"]?)(\w+)\1[\s\S]*?\n\s*\2\b/g, "<<HEREDOC");
    return cmd.replace(/'[^']*'|"(?:\\[^\n]|[^"\\])*"/g, "''");
  }
  function classifyBash(cmd) {
    cmd = stripQuoted(cmd);
    var own = /tools\/matrix\.py\s+((?:observe|orient|decide|act)\.[\w-]+)/.exec(cmd);
    if (own) return own[1];
    if (/\bgit\s+(commit|push|merge)\b/.test(cmd)) return "act.ship";
    if (/tools\/check-[\w-]+\.py/.test(cmd) && !/\bgit\s+(add|commit)\b|>\s*\S/.test(cmd)) return "decide.gate";
    var parts = cmd.split(/&&|\|\||;|\||\n/).filter(function (p) { return p.trim(); }).map(function (p) { return p.replace(/^\s*(do|then|else)\s+/, ""); });
    parts = parts.filter(function (p) { return !/^\s*(for|while|if|done|fi)\b/.test(p); });
    if (parts.length && parts.every(function (p) { return READ_ONLY.test(p) || p.trim().indexOf("cd ") === 0; }) && cmd.indexOf(">") < 0) return "observe.read";
    return "act.write";
  }
  function lookup(tool, input, vfs) {
    if (tool === "Bash") return classifyBash(String(input.command === undefined ? "" : input.command));
    var data = JSON.parse(vfs.read(".claude/cardinal-map.json")).cardinals, keys = [tool];
    if (tool === "Agent") keys.unshift("Agent:" + (input.subagent_type || "general-purpose"));
    if (tool === "Skill") keys.unshift("/" + String(input.skill === undefined ? "" : input.skill).split(":").pop());
    if (tool === "Read") { var fp = String(input.file_path === undefined ? "" : input.file_path); keys.unshift("Read:" + fp.split("/localDNS/").pop()); }
    for (var k = 0; k < keys.length; k++) {
      var cards = Object.keys(data);
      for (var c = 0; c < cards.length; c++) {
        var methods = data[cards[c]].methods, mnames = Object.keys(methods);
        for (var m = 0; m < mnames.length; m++) if (methods[mnames[m]].indexOf(keys[k]) >= 0) return cards[c] + "." + mnames[m];
      }
    }
    return "";
  }
  function isoNow(sec) { return new Date(sec * 1000).toISOString().replace(/\.\d+Z$/, "Z"); }
  function hookCardinal(c) {
    var vfs = c.vfs, ROOT = c.root, data = c.payload, now = c.now;
    var jout = function (o) { return { code: 0, stdout: JSON.stringify(o), stderr: "" }; };
    var deny = function (why) { return jout({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: why } }); };
    try {
      var tool = data.tool_name === undefined ? "" : data.tool_name, tin = data.tool_input || {};
      var alias = lookup(tool, tin, vfs);
      var line = alias ? "cardinal: " + alias : "cardinal: UNMAPPED (" + tool + ") — add it to .claude/cardinal-map.json";
      var key = String(data.tool_use_id || tool || "unknown").replace(/[^\w.-]/g, "_").slice(0, 120);
      vfs.write(".claude/.matrix-starts/" + key, now() + "\t" + (alias || "UNMAPPED"));
      var off = vfs.exists(".claude/.matrix-off");
      if (tool === "Agent" && !off) vfs.append(".claude/.agent-ledger", "launch\t" + (data.tool_use_id || "unknown") + "\n");
      if (data.agent_type) line += " · agent: " + data.agent_type;
      if (!off) {
        var poll = HARD_POLL_TOOLS.indexOf(tool) >= 0;
        var cmd_ = tool === "Bash" ? String(tin.command === undefined ? "" : tin.command) : "";
        var destructive = !!cmd_ && HARD_BASH.test(cmd_);
        if (poll || destructive)
          return deny(poll ? tool + " polls PR, CI or notification state. PR and CI events arrive on their own; polling is banned."
            : "Destructive shell command banned in every mode (hard guard). Use a non-destructive form, or ask the user to run it.");
      }
      var out = { hookEventName: "PreToolUse", additionalContext: line };
      var cfg = JSON.parse(vfs.read(".claude/cardinal-map.json"));
      var mode = (c.env && c.env.MATRIX_MODE) || cfg.mode || "name";
      var target = (cfg.repoint || {})[tool];
      if (off) mode = "name";
      if (target && mode === "warn") out.additionalContext = line + " — Matrix route: " + target;
      var lease = ".claude/.matrix-lease/" + tool;
      if (target && mode === "enforce" && vfs.exists(lease)) {
        vfs.unlink(lease);
        out.additionalContext = line + " — fallback lease consumed: the Matrix call timed out, native " + tool + " allowed once";
        target = null;
      }
      if (target && mode === "enforce") {
        out.permissionDecision = "deny";
        out.permissionDecisionReason = "The Matrix gates native " + tool + " (" + alias + "). Use: cd " + ROOT + " && " + target + ". Kill switch: touch .claude/.matrix-off";
      }
      var eg = cfg.egress || {};
      var cmd = tool === "Bash" ? stripQuoted(String(tin.command === undefined ? "" : tin.command)) : "";
      if (tool === "Bash" && cmd && !off) {
        var fileVerb = FILE_VERB.exec(cmd), fileMatrix = ROUTED_FILE_METHOD.exec(cmd);
        if (fileVerb || fileMatrix) {
          var routed = !!fileMatrix;
          vfs.append(".claude/.matrix-hitrate", (routed ? "routed" : "raw") + "\t" + (fileVerb ? fileVerb[1] : "matrix") + "\n");
          if (!routed && vfs.exists(".claude/.file-route-enforce"))
            return deny(fileVerb[1] + " is a raw file read or write, and file-route enforce is on. Route it through the Matrix, e.g. python3 tools/matrix.py observe.read PATH. Kill switch: rm the .claude/.file-route-enforce file");
          if (!routed && mode === "warn")
            out.additionalContext += " — MATRIX ROUTE: " + fileVerb[1] + " is a raw file read or write. Route it through the Matrix, e.g. python3 tools/matrix.py observe.read PATH (see observe.hitrate for the rate).";
        }
      }
      var kind = (eg.tools || {})[tool] || null;
      if (!kind) {
        var bp = Object.keys(eg.bash || {});
        for (var i = 0; i < bp.length; i++) if (new RegExp(bp[i]).test(cmd) && cmd.indexOf("tools/matrix.py") < 0) { kind = eg.bash[bp[i]]; break; }
      }
      if (kind) {
        var pf = ".claude/.matrix-probes/" + kind, fresh = false;
        if (vfs.exists(pf)) fresh = now() - vfs.mtime(pf) < (eg.fresh_seconds === undefined ? 600 : eg.fresh_seconds) && vfs.read(pf).indexOf("ok") === 0;
        if (!fresh) {
          var fs_ = eg.fresh_seconds === undefined ? 600 : eg.fresh_seconds;
          var probeCmd = { push: "observe.probe push", merge: "observe.probe merge BRANCH" }[kind] || "orient.probe  (or observe.probe / decide.probe / act.probe, whichever fits the goal)";
          out.additionalContext += " — EGRESS WITHOUT A PROBE: this call changes something outside the session and no passing '" + kind + "' probe is on record from the last " + Math.floor(fs_ / 60) + " minutes. The probe is lane 0 of 1 + N. Run it first: cd " + ROOT + " && python3 tools/matrix.py " + probeCmd;
        }
      }
      if (tool === "Bash" && alias) {
        var want = { observe: "O", orient: "OO", decide: "D", act: "A" }[alias.split(".")[0]];
        var said = String(tin.description === undefined ? "" : tin.description);
        if (want && !new RegExp("^" + want + " · \\S").test(said))
          out.additionalContext += " — LETTER: this call is " + alias + "; its description must start with '" + want + " · ' (O observe, OO orient, D decide, A act). One command, one letter.";
      }
      if (cmd && /\bgit\s+push\b[^|;&\n]*[\s:]main(?![-\w/])/.test(cmd))
        out.additionalContext += " — PUSH TO MAIN: main is kept empty on purpose and takes the founder's promotions only. Work lands on leader, by pull request from your own branch. Do not run this push.";
      var slow = cmd ? (cmd.match(/matrix\.py\s+(?:act\.ship|decide\.rehearse|decide\.gate)\b|\bgit\s+push\b/g) || []).length : 0;
      if (slow > 1)
        out.additionalContext += " — SLOW CHAIN: this call chains " + slow + " slow steps (ship, rehearse, gate, push). Each takes 3 to 6 seconds; together they break the 10-second cap. Run one per call.";
      try {
        var trail = [];
        if (vfs.exists(".claude/.matrix-recent")) trail = JSON.parse(vfs.read(".claude/.matrix-recent"));
        trail = trail.concat([alias ? alias.split(".")[0] : "unmapped"]).slice(-20);
        vfs.write(".claude/.matrix-recent", JSON.stringify(trail));
        var run = 0;
        for (var t = trail.length - 1; t >= 0; t--) { if (trail[t] !== "act") break; run++; }
        if (alias.indexOf("act.") === 0 && run >= 3)
          out.additionalContext += " — ACT RUN: " + run + " act calls in a row with no observe or orient between them. Look before the next act: cd " + ROOT + " && python3 tools/matrix.py orient.probe";
      } catch (e) { }
      var stalls = vfs.list(".claude/.matrix-stalls").filter(function (n) { return /\.json$/.test(n); });
      if (stalls.length)
        out.additionalContext += " — OPEN MATRIX STALL (" + stalls.length + "): a Matrix call breached the 10 s cap. Diagnose why the alias stalled and improve it before other work: cd " + ROOT + " && python3 tools/matrix.py orient.stall";
      return jout({ hookSpecificOutput: out });
    } catch (exc) {
      try { vfs.append(".claude/.matrix-errors", isoNow(now()) + "\t" + (exc && exc.name) + ": " + (exc && exc.message) + "\n"); } catch (e) { }
      var modeNow = (c.env && c.env.MATRIX_MODE) || "";
      if (!modeNow) { try { modeNow = JSON.parse(vfs.read(".claude/cardinal-map.json")).mode || "name"; } catch (e) { modeNow = "name"; } }
      if (modeNow === "enforce" && !vfs.exists(".claude/.matrix-off"))
        return deny("The Matrix could not judge this call (" + (exc && exc.name) + "). Fail-closed in enforce mode. Check .claude/.matrix-errors; kill switch: touch .claude/.matrix-off");
      return { code: 0, stdout: "", stderr: "" };
    }
  }

  stripQuoted = traced("cardinal.py", "strip_quoted", stripQuoted);
  classifyBash = traced("cardinal.py", "classify_bash", classifyBash);
  lookup = traced("cardinal.py", "lookup", lookup);
  hookCardinal = traced("cardinal.py", "main", hookCardinal);

  /* ------------------------------------------------------------ PostToolUse: timing.py */
  function hookTiming(c) {
    var vfs = c.vfs, now = c.now, data = c.payload, CAP = 10;
    try {
      var key = String(data.tool_use_id || data.tool_name || "unknown").replace(/[^\w.-]/g, "_").slice(0, 120), stamp = ".claude/.matrix-starts/" + key;
      if (!vfs.exists(stamp)) return { code: 0, stdout: "", stderr: "" };
      var raw = vfs.read(stamp), tab = raw.indexOf("\t"), started = raw.slice(0, tab), alias = raw.slice(tab + 1);
      vfs.unlink(stamp);
      var secs = now() - parseFloat(started), tool = data.tool_name || "unknown";
      vfs.append(".claude/.matrix-times", isoNow(now()) + "\t" + tool + "\t" + alias.trim() + "\t" + secs.toFixed(3) + "\n");
      if (secs > CAP)
        return { code: 0, stderr: "", stdout: JSON.stringify({ hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: "10-SECOND BREACH: native " + tool + " (" + alias.trim() + ") took " + secs.toFixed(1) + " s. A breach is a defect: say what made it slow and bound or split the call. Totals: cd " + c.root + " && python3 tools/matrix.py observe.times" } }) };
    } catch (e) { }
    return { code: 0, stdout: "", stderr: "" };
  }

  /* ------------------------------------------------------------ SessionStart: refeed.sh, Stop: momentum.sh, PreToolUse(Bash): gate.sh */
  function hookRefeed(c) {
    var src = c.payload.source || "startup";
    if (src !== "startup" && src !== "clear") return { code: 0, stdout: "", stderr: "" };
    var syncNote = "sync: snapshot " + (c.head || "").slice(0, 7) + "; no network here, so not compared with origin";
    if (!c.head) syncNote = "sync: no git state available here";
    var rev = c.rev || "unknown", text;
    try { text = c.vfs.read(".claude/hooks/refeed.sh"); } catch (e) { return { code: 0, stdout: "", stderr: "" }; }
    var m = /read -r -d '' ctx <<EOF \|\| true\n([\s\S]*?)\nEOF\n/.exec(text);
    if (!m) return { code: 0, stdout: "", stderr: "" };
    var ctx = m[1].split("$sync_note").join(syncNote).split("$rev").join(rev).split("$src").join(src);
    return { code: 0, stdout: JSON.stringify({ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: ctx } }), stderr: "" };
  }
  function hookMomentum(c) {
    var vfs = c.vfs, ARM = ".claude/.momentum-on", STATE = ".claude/.momentum-state", MAX = 10;
    if (!vfs.exists(ARM)) return { code: 0, stdout: "", stderr: "" };
    var allow = function () { vfs.unlink(ARM); vfs.unlink(STATE); return { code: 0, stdout: "", stderr: "" }; };
    var count = 0, lastsha = "";
    if (vfs.exists(STATE)) { var f = (splitlines(vfs.read(STATE))[0] || "").split(/\s+/).filter(Boolean); count = f[0] && /^\d+$/.test(f[0]) ? parseInt(f[0], 10) : 0; lastsha = f[1] || ""; }
    var head = c.head || "none";
    if (count >= MAX) return allow();
    if (lastsha && head === lastsha) return allow();
    count += 1;
    vfs.write(STATE, count + " " + head + "\n");
    var reason = "AUTO-MOMENTUM " + count + "/" + MAX + ": keep going — do the next unblocked item in docs/ai-cto/context.md section \"Default next actions\", ship it as a verified, pushed change, then continue. STOP the loop YOURSELF the instant you are blocked, awaiting the founder, or the queue is empty, by running: rm -f " + ARM + ". Anything irreversible or outward-facing (deletes, force-pushes, external sends, real customer data) still needs a confirm first.";
    return { code: 0, stdout: JSON.stringify({ decision: "block", reason: reason }), stderr: "" };
  }
  function hookGate(c) {
    var d = c.payload;
    if (c.vfs.exists(".claude/.gate-off")) return { code: 0, stdout: "", stderr: "" };
    if (d.tool_name !== "Bash") return { code: 0, stdout: "", stderr: "" };
    var cmd = (d.tool_input || {}).command || "";
    if (!/(^|[;&|\s])git\s+(-\S+\s+)*commit(\s|$)/.test(cmd)) return { code: 0, stdout: "", stderr: "" };
    return { code: 2, stdout: "", stderr: "COMMIT GATE — blocked. The static checks that gate a commit cannot run in this browser view, so a commit is not allowed from here. Run the commit in a real checkout, where .claude/hooks/gate.sh runs them." };
  }

  hookTiming = traced("timing.py", "main", hookTiming);
  hookRefeed = traced("refeed.sh", "main", hookRefeed);
  hookMomentum = traced("momentum.sh", "main", hookMomentum);
  hookGate = traced("gate.sh", "main", hookGate);

  /* ------------------------------------------------------------ the runner: .claude/settings.json decides what runs */
  var REGISTRY = { "decide-act.py": hookDecideAct, "cardinal.py": hookCardinal, "timing.py": hookTiming, "refeed.sh": hookRefeed, "momentum.sh": hookMomentum, "gate.sh": hookGate };

  function create(opts) {
    var root = opts.root || "/repo", nowFn = opts.now || function () { return Date.now() / 1000; };
    var vfs = makeVfs(opts.files, nowFn), cfg = JSON.parse(vfs.read(".claude/settings.json"));
    return {
      vfs: vfs,
      /* audit(text): run decide-act's rules on a reply without blocking anything, for the trace only.
         Used on the second Stop pass, where the real hook returns at once because stop_hook_active is set. */
      audit: function (text) {
        var steps = [], prevTR = TR; TR = steps; DEPTH = 0;
        var t0 = (typeof performance !== "undefined" ? performance.now() : Date.now()), reasons;
        try { reasons = review(text, vfs); } catch (e) { reasons = ["AUDIT ERROR: " + (e && e.message)]; }
        finally { TR = prevTR; DEPTH = 0; }
        return { reasons: reasons, steps: steps, t0: t0, t1: (typeof performance !== "undefined" ? performance.now() : Date.now()) };
      },
      /* returns [{command, ran, status: "ran"|"no_port"|"error", code, stdout, stderr}], the same shape the Python shim returned */
      run: function (event, payload, matcherValue, extra) {
        var results = [];
        ((cfg.hooks || {})[event] || []).forEach(function (grp) {
          var mOk = !grp.matcher || new RegExp("^(?:" + grp.matcher + ")$").test(matcherValue || "");
          if (opts.trace && grp.matcher) (results.matchers = results.matchers || []).push({ matcher: grp.matcher, value: matcherValue || "", matched: mOk });
          if (!mOk) return;
          (grp.hooks || []).forEach(function (h) {
            if (h.type !== "command") return;
            var mm = /([^\/\s"']+\.(?:py|sh))["']?\s*$/.exec(h.command || ""), base = mm ? mm[1] : "", impl = REGISTRY[base];
            if (!impl) { results.push({ command: h.command, ran: "", status: "no_port", code: null, stdout: "", stderr: "no JavaScript port for " + (base || h.command) }); return; }
            var steps = opts.trace ? [] : null, prevTR = TR; TR = steps; DEPTH = 0;
            if (steps) step("settings", ".claude/settings.json › hooks." + event, "command: " + h.command + "  →  " + base + " (JS port)");
            var hT0 = (typeof performance !== "undefined" ? performance.now() : Date.now());
            try {
              var r = impl({ payload: payload, vfs: vfs, root: root, now: nowFn, head: opts.head || "", rev: opts.rev || "", env: (extra && extra.env) || {}, transcript: extra && extra.transcript });
              results.push({ command: h.command, ran: base + " (JS port)", status: "ran", code: r.code, stdout: r.stdout || "", stderr: r.stderr || "", steps: steps, t0: hT0, t1: (typeof performance !== "undefined" ? performance.now() : Date.now()) });
            } catch (e) {
              results.push({ command: h.command, ran: base + " (JS port)", status: "error", code: 1, stdout: "", stderr: (e && e.name) + ": " + (e && e.message), steps: steps, t0: hT0, t1: (typeof performance !== "undefined" ? performance.now() : Date.now()) });
            } finally { TR = prevTR; DEPTH = 0; }
          });
        });
        return results;
      }
    };
  }
  return { create: create, review: review, lastAssistantText: lastAssistantText, pyrepr: pyrepr, sha256hex: sha256hex, splitlines: splitlines, makeVfs: makeVfs };
});
