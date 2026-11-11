#!/usr/bin/env bash
# PostToolUse(Edit|Write|MultiEdit) hook — lint as we code.
#
# The commit gate (gate.sh) lints the whole tree, but only at commit time, and by
# then a finding has been written, read past, and built on. This runs on the file
# just edited: a new finding is reported to the model in the same turn, while the
# code is still in its head. Rules live in ruff.toml (one source for both hooks).
#
# On findings: exit 2, so stderr goes back to the model and it fixes them now.
# A hook that BREAKS (no ruff, unreadable payload) exits 0 and says so — the same
# asymmetric policy as gate.sh: broken plumbing must not wedge editing.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

payload="$(cat 2>/dev/null)" || exit 0
[ -z "$payload" ] && exit 0

f="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print((d.get("tool_input") or {}).get("file_path", ""))
' 2>/dev/null)" || exit 0

case "$f" in
    *.py) ;;
    *) exit 0 ;;
esac
[ -f "$f" ] || exit 0

if ! command -v ruff >/dev/null 2>&1; then
    echo "lint: ruff not on PATH — per-edit lint SKIPPED for $f (pip install ruff)" >&2
    exit 0
fi

if ! out="$(ruff check --no-cache --config ruff.toml --output-format concise "$f" 2>&1)"; then
    cat >&2 <<MSG
LINT — findings in $f (rules: ruff.toml). Fix them now, in this edit, not at commit:
$out
MSG
    exit 2
fi
exit 0
