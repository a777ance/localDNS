// Builds a clean, committed copy of this working tree (tracked and untracked files) and returns its path,
// so the Python hooks can be run against exactly the files the JS port sees, without touching the real repo.
const { execFileSync } = require("child_process"), fs = require("fs"), os = require("os"), path = require("path");
const root = path.resolve(__dirname, "../../..");
const dst = fs.mkdtempSync(path.join(os.tmpdir(), "hooks-parity-"));
for (const f of execFileSync("git", ["ls-files", "-z", "-c", "-o", "--exclude-standard"], { cwd: root }).toString().split("\0").filter(Boolean)) {
  const to = path.join(dst, f); fs.mkdirSync(path.dirname(to), { recursive: true }); try { fs.copyFileSync(path.join(root, f), to); } catch (_) { }
}
const g = (...a) => execFileSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", ...a], { cwd: dst, stdio: "ignore" });
g("init", "-q"); g("add", "-A"); g("commit", "-qm", "parity snapshot");
module.exports = dst;
