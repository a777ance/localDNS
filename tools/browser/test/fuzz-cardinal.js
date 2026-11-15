const { spawnSync, execFileSync } = require("child_process");
const fs = require("fs"), path = require("path");
const H = require("../hooks.js");
const REPO = require("./repo-copy.js");
const files = {}; (function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (e.name === ".git") continue; const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else if (e.isFile()) { try { files[path.relative(REPO, p)] = new TextDecoder("utf-8", { fatal: true }).decode(fs.readFileSync(p)); } catch (_) { } } } })(REPO);
const head = execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO }).toString().trim();
let clock = 5000000; const rt = H.create({ files, head, root: "/repo", now: () => clock });
let seed = 777; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff, pick = (a) => a[Math.floor(rnd() * a.length)];
const FR = ["ls", "cat README.md", "grep -r foo .", "git status", "git log --oneline", "git diff", "git push origin leader", "git push origin main", "git push -f origin x", "git push --force origin x", "git push --force-with-lease", "git commit -m 'msg'", "git merge x", "git add -A", "git reset --hard", "git clean -fd", "rm -rf x", "rm x", "rm -r y", "python3 tools/check-docs.py", "python3 tools/check-all.sh", "python3 tools/matrix.py observe.read A", "python3 tools/matrix.py act.ship m f --push", "python3 tools/matrix.py decide.gate", "python3 tools/matrix.py observe.probe path", "sed -i s/a/b/ f", "awk '{print}' f", "echo hi", "echo \"rm -rf /\"", "echo 'git push --force'", "cat <<'EOF'\nrm -rf /\nEOF", "cat <<EOF\ngit push origin main\nEOF", "cd /x", "for f in a b; do ls; done", "while true; do ls; done", "if true; then ls; fi", "touch a", "cp a b", "mv a b", "tee f", "dd if=x of=y", "mkfs.ext4 /dev/x", "shutdown now", "docker system prune", "docker rm -f c", "tail -5 f | wc -l", "find . -name x", "test -f a", "env", "pwd", "date", "true", "curl http://x", "npm test", "make", "> out.txt", "2>&1", "&&", "||", ";", "|"];
let fail = 0, total = 0;
for (let i = 0; i < 300; i++) {
  const n = 1 + Math.floor(rnd() * 4), cmd = Array.from({ length: n }, () => pick(FR)).join(pick([" && ", " ; ", " | ", "\n", " || ", " > f && "]));
  const input = { command: cmd }; if (rnd() < 0.5) input.description = pick(["O · look", "OO · think", "D · gate", "A · do", "something", ""]);
  const payload = { session_id: "s", tool_name: "Bash", tool_input: input, tool_use_id: "f" + i };
  const r = spawnSync("python3", [REPO + "/.claude/hooks/cardinal.py"], { input: JSON.stringify(payload), cwd: REPO, encoding: "utf8", env: Object.assign({}, process.env, { CLAUDE_PROJECT_DIR: REPO }) });
  const pj = r.stdout.trim() ? JSON.stringify(JSON.parse(r.stdout.split(REPO).join("/repo"))) : "";
  const j = rt.run("PreToolUse", payload, "Bash").find((x) => x.ran.startsWith("cardinal")), jj = j.stdout.trim() ? JSON.stringify(JSON.parse(j.stdout)) : "";
  total++; if (pj !== jj) { fail++; if (fail <= 3) console.log("DIFF on " + JSON.stringify(input) + "\n python: " + pj.slice(0, 400) + "\n js    : " + jj.slice(0, 400)); }
}
console.log(`${total - fail}/${total} fuzzed Bash calls identical`);
process.exit(fail ? 1 : 0);
