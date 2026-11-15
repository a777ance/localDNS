#!/usr/bin/env python3
"""build.py — builds the repo explorer page (the claude.ai artifact) from this repo.

    python3 tools/browser/explorer/build.py [OUT_DIR]      (default: /tmp/localdns-explorer)

Writes three files, ready to publish as the artifact's own files:
  index.html  the page: index.template.html with tools/browser/hooks.js and browser_shim.py embedded
  repo.json   every tracked text file at HEAD of the working tree, plus branch, commit and the CLAUDE.md revision
  bin.json    the tracked binary files (images), base64, loaded only when one is opened
  heads.json  the first 800 characters of every text file, so a mail turn can start before repo.json loads

The artifact declares two capabilities, set with the artifact tools, not here: sample (Claude in the page)
and db (the mailbox, tools/telepathy/ARTIFACT-BUS.md). Standard library only.
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/localdns-explorer")
    out.mkdir(parents=True, exist_ok=True)
    page = (HERE / "index.template.html").read_text(encoding="utf-8")
    hooks = (ROOT / "tools/browser/hooks.js").read_text(encoding="utf-8")
    shim = (HERE / "browser_shim.py").read_text(encoding="utf-8")
    for name, text in (("hooks.js", hooks), ("browser_shim.py", shim)):
        if "</script" in text:
            sys.exit(f"FAILED: {name} contains '</script', which would end the page's script early")
    page = page.replace("/*@@HOOKS_JS@@*/", hooks, 1).replace("#@@BROWSER_SHIM@@", shim, 1)
    if "@@HOOKS_JS@@" in page or "@@BROWSER_SHIM@@" in page:
        sys.exit("FAILED: a placeholder was not filled")
    files, bins = [], {}
    for p in [p for p in subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0") if p]:
        fp = ROOT / p
        if fp.is_symlink() or not fp.is_file():
            files.append({"p": p, "s": 0, "t": "", "k": "link"})
            continue
        b = fp.read_bytes()
        try:
            files.append({"p": p, "s": len(b), "t": b.decode("utf-8")})
        except UnicodeDecodeError:
            files.append({"p": p, "s": len(b), "k": "bin"})
            bins[p] = base64.b64encode(b).decode()
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    base = os.environ.get("EXPLORER_BASE", "leader 71e6ccc")
    data = {"repo": "a777ance/localDNS", "branch": branch if branch == "leader" else f"{branch} (on {base})",
            "commit": git("log", "-1", "--format=%h %cs %s"), "head": git("rev-parse", "HEAD"),
            "claude_md_rev": git("log", "-1", "--format=%h %ci", "--", "CLAUDE.md"), "files": files}
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "repo.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    (out / "bin.json").write_text(json.dumps(bins, separators=(",", ":")), encoding="utf-8")
    heads = {"repo": data["repo"], "heads": {f["p"]: f["t"][:800] for f in data["files"] if f.get("k") != "bin" and isinstance(f.get("t"), str)}}
    (out / "heads.json").write_text(json.dumps(heads, separators=(",", ":")), encoding="utf-8")
    dirty = git("status", "--porcelain")
    print(f"ok   explorer: {len(files)} files ({len(bins)} binary) at {data['commit'][:60]} -> {out}")
    if dirty:
        print("note the working tree has uncommitted changes; repo.json holds them, but the commit shown does not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
