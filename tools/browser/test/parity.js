// Differential test: the same inputs through the real Python hooks and the JS port; compare exactly.
const { spawnSync, execFileSync } = require("child_process");
const fs = require("fs"), path = require("path"), crypto = require("crypto");
const H = require("../hooks.js");
const REPO = require("./repo-copy.js");

function loadFiles() {
  const out = {}; (function walk(d) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.name === ".git") continue;
      const p = path.join(d, e.name);
      if (e.isDirectory()) walk(p); else if (e.isFile()) { const b = fs.readFileSync(p); try { out[path.relative(REPO, p)] = new TextDecoder("utf-8", { fatal: true }).decode(b); } catch (_) { } }
    }
  })(REPO); return out;
}
const files = loadFiles();
const head = execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO }).toString().trim();
let clock = 1000000; const now = () => clock;
const rev = execFileSync("git", ["log", "-1", "--format=%h %ci", "--", "CLAUDE.md"], { cwd: REPO }).toString().trim();
const rt = H.create({ files, head, rev, root: "/repo", now });

function py(script, input, env) {
  const r = spawnSync("python3", [path.join(REPO, script)], { input, cwd: REPO, encoding: "utf8", env: Object.assign({}, process.env, { CLAUDE_PROJECT_DIR: REPO, SNAPSHOT_REV: "71e6ccc 2026-11-12" }, env || {}) });
  return { code: r.status, stdout: r.stdout, stderr: r.stderr };
}
let fails = 0, total = 0;
function check(name, a, b) { total++; if (a !== b) { fails++; console.log("DIFF  " + name + "\n  python: " + JSON.stringify(a).slice(0, 500) + "\n  js    : " + JSON.stringify(b).slice(0, 500)); } }

/* ---------------- Stop: decide-act ---------------- */
const L = (n) => "**Landed · N = " + n + ":** done.";
const replies = {
  compliant: "**Done.** ok.\n\nStopping because: read-only.\n\n" + L(1),
  noLead: "Here is the answer.\n\nStopping because: x.\n\n" + L(1),
  noLanding: "**Done.** ok.\n\nStopping because: x.",
  both: "plain",
  leadPunct: "**Partial**: half.\n\nStopping because: x.\n\n" + L(2),
  leadWait: "**Waiting.** on founder\n\nStopping because: x.\n\n" + L(1),
  hedge: "**Done.** It should work now.\n\nStopping because: x.\n\n" + L(1),
  hedgeInCode: "**Done.** run `it should work` here.\n\nStopping because: x.\n\n" + L(1),
  hedgeQuoted: "**Done.** he said \"should be fine\" earlier.\n\nStopping because: x.\n\n" + L(1),
  hedgeMulti: "**Done.** Probably works and might have worked.\n\nStopping because: x.\n\n" + L(1),
  noStopNoNext: "**Done.** ok.\n\n" + L(1),
  decide3act1: "**Done.**\n\nDecide\n1. one\n2. two\n3. three\n\nAct\n- did one\n\nStopping because: x.\n\n" + L(3),
  decide2act2: "**Done.**\n\n**Decide**\n1. one\n2. two\n\n**Act**\n1. did one\n2. did two\n\nStopping because: x.\n\n" + L(2),
  decideNoAct: "**Done.**\n\nDecide:\n1. alpha\n2. beta\n\nStopping because: x.\n\n" + L(2),
  decideHeadings: "**Done.**\n\n## Decide\n1. a\n2. b\n\n## Act\n- x\n- y\n\n## Orient\nmore\n\nStopping because: z.\n\n" + L(2),
  bashNoCd: "**Done.**\n\n```bash\nls -la\n```\n\nStopping because: x.\n\n" + L(1),
  bashCdUser: "**Done.**\n\n```bash\ncd /home/user/localDNS\nls\n```\n\nStopping because: x.\n\n" + L(1),
  bashGood: "**Done.**\n\n```bash\ncd ~/localDNS\npython3 tools/check-all.sh\n```\n\nNot rehearsed: no checkout here.\n\nStopping because: x.\n\n" + L(1),
  bashGoodNoRehearse: "**Done.**\n\n```bash\ncd ~/localDNS && git pull --ff-only\n```\n\nStopping because: x.\n\n" + L(1),
  bashGoodNoRehearse2: "**Done.**\n\n```bash\ncd ~/localDNS\n# comment\ngit pull --ff-only\n```\n\nStopping because: x.\n\n" + L(1),
  tileMissing: "**Done.**\n\nDECISION · DEC-099\nDecision needed: yes\n\nStopping because: x.\n\n" + L(1),
  tileKnown: "**Done.**\n\nDECISION · DEC-015\nAction if GO: a\nAction if NO GO: b\nDecision needed: c\n\nStopping because: x.\n\n" + L(1),
  lWording: "**Done.**\n\n## Still open\n- a thing\n\nStopping because: x.\n\n" + L(1),
  lItems: "**Done.**\n\nL · what is left\n- fix the thing\n- DEC-014 founder call\n- sub-loop running: abc\n1. numbered loop item\n\nStopping because: x.\n\n" + L(3),
  lItemsBreak: "**Done.**\n\nL · open\n- loop item\n## Next\n- not in L\n\nStopping because: x.\n\n" + L(1),
  unicode: "**Done.** café — ünïcode ✓ “quoted”\n\nStopping because: x.\n\n" + L(1),
  leadingBlank: "\n\n**Done.** ok\n\nStopping because: x.\n\n" + L(1),
  emptyish: "   \n",
  landedWrongFormat: "**Done.** ok.\n\nStopping because: x.\n\n**Landed: 1** done",
  landedNoSpace: "**Done.** ok.\n\nStopping because: x.\n\n**Landed · N = 2:**",
  trailingBlank: "**Done.** ok.\n\nStopping because: x.\n\n" + L(1) + "\n\n\n",
  longFirst: "**Done" + "x".repeat(120) + "\n\nStopping because: x.\n\n" + L(1),
  quoteInFirst: "It's \"odd\" and it's wrong\n\nStopping because: x.\n\n" + L(1),
  letterDecideNothingActed: "**Waiting.**\n\nD · Queued.\n1. Run A\n2. Run B\n\nA · Nothing run yet.\n\nStopping because: x.\n\n" + L(2),
  letterDecideActed: "**Done.**\n\nD · Queued.\n1. Run A\n2. Run B\n\nA · Ran.\n1. A ran.\n2. B ran.\n\nStopping because: x.\n\n" + L(2),
  letterActEndsAtL: "**Partial.**\n\nD · Queued.\n1. a\n2. b\n\nA · One.\n- a ran\n\nL · Open.\n- DEC-015 waits\n- DEC-015 again\n\nStopping because: x.\n\n" + L(2),
  letterBoldSteps: "**Done.**\n\n**D ·** Queued.\n1. a\n\n**A ·** Ran.\n- a ran\n\nStopping because: x.\n\n" + L(1),
  letterMultiReport: "**Done.**\n\nD · Queued.\n1. a\n2. b\n\nA A O · ran two then looked\n\nStopping because: x.\n\n" + L(2),
  decideInProse: "**Done.** We Decided things.\nDecide how\n1. only\n\nStopping because: x.\n\n" + L(1),
};
const mkTranscript = (t) => [{ type: "user", message: { role: "user", content: "q" } }, { type: "assistant", message: { role: "assistant", content: [{ type: "text", text: t }] } }];
for (const [name, text] of Object.entries(replies)) {
  const recs = mkTranscript(text);
  const tp = "/tmp/par-transcript.jsonl"; fs.writeFileSync(tp, recs.map((r) => JSON.stringify(r)).join("\n") + "\n");
  const p = py(".claude/hooks/decide-act.py", JSON.stringify({ session_id: "s", transcript_path: tp, stop_hook_active: false }));
  const pr = p.stdout.trim() ? JSON.parse(p.stdout).reason : "";
  const j = rt.run("Stop", { session_id: "s", hook_event_name: "Stop", stop_hook_active: false }, "", { transcript: recs }).find((r) => r.ran.startsWith("decide-act"));
  const jr = j.stdout.trim() ? JSON.parse(j.stdout).reason : "";
  check("decide-act/" + name, pr, jr);
}
// stop_hook_active and string-content and multi-block transcripts
{
  const p = py(".claude/hooks/decide-act.py", JSON.stringify({ stop_hook_active: true, transcript_path: "/tmp/par-transcript.jsonl" }));
  const j = rt.run("Stop", { stop_hook_active: true }, "", { transcript: mkTranscript("plain") }).find((r) => r.ran.startsWith("decide-act"));
  check("decide-act/stop_hook_active", p.stdout.trim(), j.stdout.trim());
  const recs = [{ role: "assistant", content: "plain string content" }, { type: "assistant", message: { role: "assistant", content: [{ type: "tool_use", name: "x" }, { type: "text", text: "**Done.** a\n\nStopping because: x.\n\n" + L(1) }, { type: "text", text: "tail" }] } }];
  fs.writeFileSync("/tmp/par-t2.jsonl", recs.map((r) => JSON.stringify(r)).join("\n") + "\n");
  const p2 = py(".claude/hooks/decide-act.py", JSON.stringify({ transcript_path: "/tmp/par-t2.jsonl" }));
  const j2 = rt.run("Stop", {}, "", { transcript: recs }).find((r) => r.ran.startsWith("decide-act"));
  check("decide-act/multiblock", p2.stdout.trim() ? JSON.parse(p2.stdout).reason : "", j2.stdout.trim() ? JSON.parse(j2.stdout).reason : "");
}

/* ---------------- PreToolUse: cardinal (state persists across calls in both) ---------------- */
const norm = (s) => s.split(REPO).join("/repo");
const calls = [
  ["Read", { file_path: "README.md" }], ["Read", { file_path: "CLAUDE.md" }], ["Read", { file_path: "/x/localDNS/tools/matrix.py" }],
  ["Glob", { pattern: "tools/*" }], ["Grep", { pattern: "foo", path: "." }], ["Write", { file_path: "a", content: "b" }], ["Edit", { file_path: "a" }],
  ["Agent", { subagent_type: "general-purpose" }], ["Agent", { subagent_type: "Explore" }], ["Skill", { skill: "orient" }], ["Skill", { skill: "x:decide" }],
  ["SomeUnmappedTool", {}], ["ReadNotifications", {}], ["mcp__github__create_pull_request", {}], ["mcp__claude-code-remote__send_message", {}],
  ["Bash", { command: "python3 tools/check-docs.py" }], ["Bash", { command: "python3 tools/check-docs.py > out.txt" }],
  ["Bash", { command: "git commit -m x" }], ["Bash", { command: "git push origin leader" }], ["Bash", { command: "git push origin main" }],
  ["Bash", { command: "git push --force origin leader" }], ["Bash", { command: "git push --force-with-lease origin leader" }], ["Bash", { command: "rm -rf /tmp/x" }],
  ["Bash", { command: "rm file" }], ["Bash", { command: "git reset --hard HEAD" }], ["Bash", { command: "dd if=/dev/zero of=x" }],
  ["Bash", { command: "ls -la && cat README.md", description: "O · look" }], ["Bash", { command: "cat a | grep b | wc -l", description: "x" }],
  ["Bash", { command: "echo hi > f" }], ["Bash", { command: "for f in a b; do ls $f; done" }], ["Bash", { command: "cd /x && sed -i s/a/b/ f" }],
  ["Bash", { command: "python3 tools/matrix.py observe.read README.md", description: "O · read" }], ["Bash", { command: "python3 tools/matrix.py act.write PATH" }],
  ["Bash", { command: "python3 tools/matrix.py act.ship \"m\" f --push", description: "A · ship" }], ["Bash", { command: "git push origin leader && python3 tools/matrix.py act.ship x" }],
  ["Bash", { command: "cat <<'EOF'\nrm -rf /\nEOF" }], ["Bash", { command: "echo \"git push --force\" " }], ["Bash", { command: "grep x f", description: "OO · orient" }],
  ["Bash", { command: "tail -5 f" }], ["Bash", { command: "touch a" }], ["Bash", { command: "touch a" }], ["Bash", { command: "touch b" }], ["Bash", { command: "cp a b" }], ["Bash", { command: "mv a b" }],
  ["Bash", { command: "ls" }], ["Bash", {}], ["Bash", { command: "git merge x" }], ["Bash", { command: "git status; git log" }], ["Bash", { command: "if true; then ls; fi" }],
];
let n = 0;
for (const [tool, input] of calls) {
  n++; const payload = { session_id: "s", hook_event_name: "PreToolUse", tool_name: tool, tool_input: input, tool_use_id: "tu_" + n };
  const p = py(".claude/hooks/cardinal.py", JSON.stringify(payload));
  const j = rt.run("PreToolUse", payload, tool).find((r) => r.ran.startsWith("cardinal"));
  const pj = p.stdout.trim() ? JSON.stringify(JSON.parse(norm(p.stdout))) : "", jj = j.stdout.trim() ? JSON.stringify(JSON.parse(j.stdout)) : "";
  check("cardinal/" + n + " " + tool + " " + JSON.stringify(input).slice(0, 60), pj, jj);
  // PostToolUse timing for the same call: no output at the speeds here; both must write one row
  const tp = { tool_name: tool, tool_use_id: "tu_" + n };
  const pt = py(".claude/hooks/timing.py", JSON.stringify(tp));
  const jt = rt.run("PostToolUse", tp, tool).find((r) => r.ran.startsWith("timing"));
  check("timing/" + n, pt.stdout.trim(), jt.stdout.trim());
}
// state files agree: hit-rate, recent trail, errors, ledger, times (columns tool+alias only)
const pyFile = (p) => { try { return fs.readFileSync(path.join(REPO, p), "utf8"); } catch (_) { return ""; } };
const jsFile = (p) => { try { return rt.vfs.read(p); } catch (_) { return ""; } };
for (const f of [".claude/.matrix-hitrate", ".claude/.agent-ledger", ".claude/.matrix-errors"]) check("state/" + f, pyFile(f), jsFile(f));
check("state/.claude/.matrix-recent (as JSON)", JSON.stringify(JSON.parse(pyFile(".claude/.matrix-recent"))), JSON.stringify(JSON.parse(jsFile(".claude/.matrix-recent"))));
const cols = (t) => t.split("\n").filter(Boolean).map((l) => l.split("\t").slice(1, 3).join("|")).join("\n");
check("state/.matrix-times", cols(pyFile(".claude/.matrix-times")), cols(jsFile(".claude/.matrix-times")));
// timing breach: a stamp older than 10 s
{
  const stamp = ".claude/.matrix-starts/slow1";
  fs.mkdirSync(path.join(REPO, ".claude/.matrix-starts"), { recursive: true });
  fs.writeFileSync(path.join(REPO, stamp), ((Date.now() / 1000) - 12.5) + "\tact.write");
  const pt = py(".claude/hooks/timing.py", JSON.stringify({ tool_name: "Bash", tool_use_id: "slow1" }));
  rt.vfs.write(stamp, (now() - 12.5) + "\tact.write");
  const jt = rt.run("PostToolUse", { tool_name: "Bash", tool_use_id: "slow1" }, "Bash").find((r) => r.ran.startsWith("timing"));
  const strip = (s) => s.trim() ? JSON.parse(norm(s)).hookSpecificOutput.additionalContext.replace(/took [\d.]+ s/, "took N s") : "";
  check("timing/breach", strip(pt.stdout), strip(jt.stdout));
}
// open stall changes cardinal and decide-act output
{
  fs.mkdirSync(path.join(REPO, ".claude/.matrix-stalls"), { recursive: true }); fs.writeFileSync(path.join(REPO, ".claude/.matrix-stalls/s1.json"), "{}");
  rt.vfs.write(".claude/.matrix-stalls/s1.json", "{}");
  const payload = { tool_name: "Read", tool_input: { file_path: "README.md" }, tool_use_id: "stall1" };
  const p = py(".claude/hooks/cardinal.py", JSON.stringify(payload)), j = rt.run("PreToolUse", payload, "Read").find((r) => r.ran.startsWith("cardinal"));
  check("cardinal/open-stall", JSON.stringify(JSON.parse(norm(p.stdout))), JSON.stringify(JSON.parse(j.stdout)));
  const recs = mkTranscript("**Done.** ok\n\n" + L(1)); fs.writeFileSync("/tmp/par-t3.jsonl", recs.map((r) => JSON.stringify(r)).join("\n") + "\n");
  const pd = py(".claude/hooks/decide-act.py", JSON.stringify({ transcript_path: "/tmp/par-t3.jsonl" })), jd = rt.run("Stop", {}, "", { transcript: recs }).find((r) => r.ran.startsWith("decide-act"));
  check("decide-act/open-stall", JSON.parse(pd.stdout).reason, JSON.parse(jd.stdout).reason);
  fs.unlinkSync(path.join(REPO, ".claude/.matrix-stalls/s1.json")); rt.vfs.unlink(".claude/.matrix-stalls/s1.json");
}

/* ---------------- SessionStart / Stop(momentum) vs the verified Python ports ---------------- */
for (const src of ["startup", "clear", "resume", "compact"]) {
  const p = py("tools/browser/refeed.py", JSON.stringify({ source: src }));
  const j = rt.run("SessionStart", { source: src }, src).filter((r) => r.ran.startsWith("refeed"))[0];
  check("refeed/" + src, p.stdout.trim() ? JSON.parse(p.stdout).hookSpecificOutput.additionalContext : "", j && j.stdout.trim() ? JSON.parse(j.stdout).hookSpecificOutput.additionalContext : "");
}
{
  // momentum: inert, then armed in both
  const m0p = py("tools/browser/momentum.py", "{}"), m0j = rt.run("Stop", {}, "", { transcript: [] }).find((r) => r.ran.startsWith("momentum"));
  check("momentum/inert", m0p.stdout.trim(), m0j.stdout.trim());
  fs.writeFileSync(path.join(REPO, ".claude/.momentum-on"), ""); rt.vfs.write(".claude/.momentum-on", "");
  const m1p = py("tools/browser/momentum.py", "{}"), m1j = rt.run("Stop", {}, "", { transcript: [] }).find((r) => r.ran.startsWith("momentum"));
  check("momentum/armed-1", JSON.stringify(JSON.parse(m1p.stdout)), JSON.stringify(JSON.parse(m1j.stdout)));
  const m2p = py("tools/browser/momentum.py", "{}"), m2j = rt.run("Stop", {}, "", { transcript: [] }).find((r) => r.ran.startsWith("momentum"));
  check("momentum/armed-2 (head unmoved -> allow)", m2p.stdout.trim(), m2j.stdout.trim());
  check("momentum/disarmed", String(fs.existsSync(path.join(REPO, ".claude/.momentum-on"))), String(rt.vfs.exists(".claude/.momentum-on")));
}
// gate: JS fails closed on commit; python (real) would run the checks. Only the non-commit paths are comparable.
for (const [tool, cmd] of [["Bash", "ls"], ["Read", ""], ["Bash", "git status"]]) {
  const payload = { tool_name: tool, tool_input: { command: cmd } };
  const p = py("tools/browser/gate.py", JSON.stringify(payload)), j = rt.run("PreToolUse", payload, "Bash").find((r) => r.ran.startsWith("gate"));
  check("gate/" + tool + ":" + cmd, p.code + "|" + p.stderr.trim(), j.code + "|" + j.stderr.trim());
}
{ const j = rt.run("PreToolUse", { tool_name: "Bash", tool_input: { command: "git commit -m x" } }, "Bash").find((r) => r.ran.startsWith("gate")); check("gate/commit blocks (code 2)", "2", String(j.code)); }
// sha256 against node's
for (const s of ["", "abc", "cd x && ls", "ünï ✓".repeat(30)]) check("sha256/" + s.slice(0, 8), crypto.createHash("sha256").update(s).digest("hex"), H.sha256hex(s));
// no_port honesty: precompact and resume have no JS port and say so
{ const r = rt.run("PreCompact", {}, "auto"); check("precompact reported as no_port", "no_port", r[0] && r[0].status); }

console.log(`\n${total - fails}/${total} identical` + (fails ? `, ${fails} DIFFER` : ""));
process.exit(fails ? 1 : 0);
