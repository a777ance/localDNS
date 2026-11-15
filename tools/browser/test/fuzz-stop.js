const { spawnSync, execFileSync } = require("child_process");
const fs = require("fs"), path = require("path");
const H = require("../hooks.js");
const REPO = require("./repo-copy.js");
const files = {}; (function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (e.name === ".git") continue; const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else if (e.isFile()) { try { files[path.relative(REPO, p)] = new TextDecoder("utf-8", { fatal: true }).decode(fs.readFileSync(p)); } catch (_) { } } } })(REPO);
const head = execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO }).toString().trim();
const rt = H.create({ files, head, root: "/repo" });
let seed = 12345; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff, pick = (a) => a[Math.floor(rnd() * a.length)];
const FR = ["**Done.** ok", "**Partial**: half", "**Blocked.**", "**Waiting**", "Done. plain", "Here you go", "## Decide", "Decide", "**Decide**", "Decided:", "1. first thing", "2. second thing", "3. third", "- bullet a", "- bullet b", "## Act", "Act", "**Act**", "Acted:", "## Orient", "**Orient**", "L · open items", "L · what is left", "- fix it", "- DEC-014 founder", "- sub-loop running: x", "## Still open", "## Limits", "## Open items",
  "```bash\ncd ~/localDNS\nls\n```", "```bash\nls\n```", "```bash\ncd /home/user/x\nls\n```", "```bash\ncd ~/localDNS && git pull\n```", "```py\nprint('should work')\n```", "It should work.", "probably works", "he said \"should be fine\"", "`should work`", "might have worked", "Not rehearsed: no box", "Stopping because: waiting", "DECISION · DEC-015", "DECISION · DEC-777", "Action if GO: a", "Action if NO GO: b", "Decision needed: c",
  "**Landed · N = 2:** x done.", "**Landed · N = 1:**", "**Landed: 2** x", "café ünï ✓", "“smart quotes”", "it's \"mixed\" 'q'", "  indented", "\t tab", "", "", "—", "**Done**:", "**Done**. x", "# Title", "### H3", "**Summary.**", "**Result**", "D · Queued", "D · Options, queued", "**D ·** Decide", "A · Nothing run", "A · Ran the queue", "**A ·** Acted", "A A O · three", "OO · Oriented", "O · Observed", "L · Open"];
let fail = 0, total = 0;
for (let i = 0; i < 400; i++) {
  const n = 2 + Math.floor(rnd() * 9), parts = []; for (let k = 0; k < n; k++) parts.push(pick(FR));
  const text = parts.join(pick(["\n", "\n", "\n\n", "\n\n\n"]));
  const recs = [{ type: "assistant", message: { role: "assistant", content: [{ type: "text", text }] } }];
  fs.writeFileSync("/tmp/fz.jsonl", JSON.stringify(recs[0]) + "\n");
  const r = spawnSync("python3", [REPO + "/.claude/hooks/decide-act.py"], { input: JSON.stringify({ transcript_path: "/tmp/fz.jsonl", session_id: "s" }), cwd: REPO, encoding: "utf8", env: Object.assign({}, process.env, { CLAUDE_PROJECT_DIR: REPO }) });
  const pr = r.stdout.trim() ? JSON.parse(r.stdout).reason : "";
  const j = rt.run("Stop", {}, "", { transcript: recs }).find((x) => x.ran.startsWith("decide-act")), jr = j.stdout.trim() ? JSON.parse(j.stdout).reason : "";
  total++; if (pr !== jr) { fail++; if (fail <= 3) console.log("DIFF on:\n" + JSON.stringify(text) + "\n python: " + JSON.stringify(pr).slice(0, 300) + "\n js    : " + JSON.stringify(jr).slice(0, 300)); }
}
console.log(`${total - fail}/${total} fuzzed replies identical`);
process.exit(fail ? 1 : 0);
