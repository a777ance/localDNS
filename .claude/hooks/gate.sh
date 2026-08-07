#!/usr/bin/env bash
# PreToolUse(Bash) hook — the commit gate.
#
# WHY THIS EXISTS (docs/architecture/warrant-sites.md):
# An invariant that lives only in CLAUDE.md has an author and no site. Briefing
# prose is read once, by the operator, outside the read path of any run — so it
# assigns nothing to a run's given-set, and a run that never sees it re-breaks it
# while following its own instructions faithfully. Citing the briefing from a
# command file transfers the citation, not the cited: `.claude/commands/cardio.md`
# referenced CLAUDE.md §G five times while its own text defined the confidence
# scale §G forbids, and the file's text won.
#
# So invariants that decide MECHANICALLY are migrated here, to the emission
# boundary. A commit is where a claim leaves the working tree and becomes the
# thing the next session inherits — the last point at which "did this earn its
# tier?" can still be answered cheaply.
#
# Runs the repo's two static checks before any `git commit`:
#   tools/check-docs.py        links + repo-path references resolve
#   tools/check-provenance.py  provenance tags valid; no unstaged R-tier deploy
#                              target; no R/A tag without a verify: route
#
# FAILURE POLICY, deliberately asymmetric:
#   * A check that FAILS blocks the commit (exit 2 — stderr goes back to the model).
#   * A hook that BREAKS (missing python, unreadable repo, malformed input) lets the
#     commit through (exit 0). A gate that wedges the repo when its own plumbing
#     breaks would be a worse failure than the one it guards.
#
# Bypass, when you genuinely need it (a WIP commit mid-repair):
#     touch .claude/.gate-off      # disable
#     rm    .claude/.gate-off      # re-arm
# Leave the bypass on and the invariant is back to having no site — so the block
# message says so, and the file is git-ignored rather than committed.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

[ -f .claude/.gate-off ] && exit 0

payload="$(cat 2>/dev/null)" || exit 0
[ -z "$payload" ] && exit 0

cmd="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if d.get("tool_name") != "Bash":
    sys.exit(0)
print(d.get("tool_input", {}).get("command", ""))
' 2>/dev/null)" || exit 0

# Only gate real commits. `git commit` appearing inside a quoted string (a commit
# MESSAGE that talks about committing, say) is matched too — over-triggering costs
# two seconds; under-triggering costs the invariant.
printf '%s' "$cmd" | grep -Eq '(^|[;&|[:space:]])git[[:space:]]+(-[^[:space:]]+[[:space:]]+)*commit([[:space:]]|$)' || exit 0

fails=""
for check in tools/check-docs.py tools/check-provenance.py; do
    [ -f "$check" ] || continue
    if ! out="$(python3 "$check" 2>&1)"; then
        fails="${fails}
── ${check} ──
$(printf '%s' "$out" | tail -20)"
    fi
done

[ -z "$fails" ] && exit 0

cat >&2 <<EOF
COMMIT GATE — blocked. A static check that decides mechanically says no.
$fails

Fix the cause, not the gate. If this check is wrong, that is a finding about the
check — change it in the same commit and say why. To bypass for a genuine WIP
commit: touch .claude/.gate-off (and remember the invariant has no site while
that file exists).
EOF
exit 2
