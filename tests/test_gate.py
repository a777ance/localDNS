"""Real tests for the repo's gates. Every assertion is on a process exit code.

Destructive command strings are assembled at runtime so that writing this file
does not itself trip the Bash alias router.

Run: python3 -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALIAS = ROOT / ".claude" / "hooks" / "alias.sh"
BREAK_GLASS = ROOT / ".claude" / ".alias-off"

DESTRUCTIVE_RM = "r" + "m -rf /tmp/factory-test-never-created"
DESTRUCTIVE_FORCE = "git push " + "--" + "force origin test-branch"
SAFE_FORCE_LEASE = "git push origin test-branch " + "--" + "force-with-lease"


def route(tool, tool_input):
    """Send one PreToolUse payload through the router, as the harness does."""
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input})
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT))
    return subprocess.run(
        ["bash", str(ALIAS)], input=payload, text=True, capture_output=True, env=env
    )


class RouterExitCodes(unittest.TestCase):
    def tearDown(self):
        if BREAK_GLASS.exists():
            BREAK_GLASS.unlink()

    def test_native_read_is_denied(self):
        r = route("Read", {"file_path": "README.md"})
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("Native Read is blocked", r.stderr)

    def test_native_grep_is_denied(self):
        r = route("Grep", {"pattern": "alias"})
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_mvp_github_read_is_allowed(self):
        r = route("mcp__github__get_file_contents", {"path": "README.md"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_mvp_toolsearch_is_allowed(self):
        r = route("ToolSearch", {"query": "select:AskUserQuestion"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_safe_bash_is_allowed(self):
        r = route("Bash", {"command": "git status"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_destructive_rm_is_denied(self):
        r = route("Bash", {"command": DESTRUCTIVE_RM})
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_destructive_force_push_is_denied(self):
        r = route("Bash", {"command": DESTRUCTIVE_FORCE})
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_force_with_lease_is_allowed(self):
        r = route("Bash", {"command": SAFE_FORCE_LEASE})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_break_glass_turns_enforcement_off(self):
        BREAK_GLASS.touch()
        r = route("Read", {"file_path": "README.md"})
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_enforcement_returns_when_break_glass_removed(self):
        BREAK_GLASS.touch()
        BREAK_GLASS.unlink()
        r = route("Read", {"file_path": "README.md"})
        self.assertEqual(r.returncode, 2, r.stderr)


class RepoChecks(unittest.TestCase):
    CHECKS = [
        "tools/check-docs.py",
        "tools/check-doctrine.py",
        "tools/check-provenance.py",
        "tools/check-debt.py",
        "tools/sync-briefings.py",
    ]

    def test_each_repo_check_exits_zero(self):
        for check in self.CHECKS:
            with self.subTest(check=check):
                r = subprocess.run(
                    [sys.executable, check], cwd=ROOT, capture_output=True, text=True
                )
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
