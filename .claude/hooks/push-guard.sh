#!/usr/bin/env bash
# PreToolUse(Bash) hook — the force-push guard.
#
# WHY THIS EXISTS (docs/architecture/proxies.md, Law 1 + the gap audit):
# "Never force-push Yggdrasil or main" (CLAUDE.md, branch policy) was enforced by NOTHING.
# The agent git proxy blocks `git push --delete` but PERMITS `git push --force` — proven
# 2026-08-08 by a successful forced update. Both orphan commits; only one is refused. That
# is a verb-scoped control guarding an effect-shaped risk, so the EFFECT gets a site here.
#
# This is the difference between a DECLARED boundary (the caller is asked to comply) and an
# ENFORCED one (an intermediary refuses). Every A777ance briefing now carries the rule; this
# file is what makes it more than a request in the repo it is installed in.
#
# Scoped by EFFECT, not verb: every spelling that rewrites a protected ref —
# --force, -f, --force-with-lease, and the `+refspec` form — against Yggdrasil or main.
# A force-push to any OTHER branch passes; this guards founder-authored shared history,
# not every rewrite.
#
# FAILURE POLICY: a matched force-push blocks (exit 2). A broken hook lets the call through
# (exit 0) — a guard that wedges the repo when its own plumbing breaks is a worse failure
# than the one it guards. Same asymmetry as gate.sh, chosen deliberately (Law 5).
#
# Bypass: touch .claude/.gate-off  (and the invariant is back to having no site).
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
[ -z "$cmd" ] && exit 0

# Quoted text is DATA, not a command: a commit message that discusses force-pushing must
# not trip this. Strip quoted spans first, then scan. A compound `git commit -m '…' &&
# git push --force origin main` still matches, because only the message is quoted.
scan="$(printf '%s' "$cmd" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")"

printf '%s' "$scan" | grep -Eq '(^|[;&|[:space:]])git([[:space:]]+-[^[:space:]]+)*[[:space:]]+push([[:space:]]|$)' || exit 0

forced=0
printf '%s' "$scan" | grep -Eq '[[:space:]](--force([[:space:]]|=|$)|--force-with-lease|-f([[:space:]]|$))' && forced=1
printf '%s' "$scan" | grep -Eq '[[:space:]]\+[A-Za-z0-9_./-]*(HEAD|Yggdrasil|main)' && forced=1
[ "$forced" = 1 ] || exit 0

# Count non-flag arguments after `push`: <remote> [refspec...]. A refspec means the target
# is EXPLICIT, so the current branch is irrelevant — `--force origin tmp/scratch` from
# Yggdrasil must pass. Only with no refspec does the push default to the current branch.
# Over-blocking is not the safe direction: a gate that refuses legitimate work gets
# switched off, and an off gate is worse than a narrow one.
args="$(printf '%s' "$scan" \
        | sed -E 's/.*git([[:space:]]+-[^[:space:]]+)*[[:space:]]+push//' \
        | tr ' ' '\n' | grep -v '^-' | grep -v '^$' | tr '\n' ' ')"
argc="$(printf '%s' "$args" | wc -w)"

if [ "$argc" -ge 2 ]; then
    target="$(printf '%s' "$args" | tr ' ' '\n' | tail -n +2 \
              | grep -oE '(Yggdrasil|main)' | head -1)"
else
    case "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" in
        Yggdrasil|main) target="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" ;;
        *) target="" ;;
    esac
fi
[ -n "$target" ] || exit 0

cat >&2 <<EOF
PUSH GUARD — blocked. Force-push to \`$target\` refuses here.

A fast-forward can only ADD commits. A forced update REWRITES the ref, orphaning whatever
it passed over — including founder-authored doctrine this session never read.
"A session transcribes doctrine; it does not author it."

The environment will NOT stop you: the agent git proxy blocks --delete but permits --force
(localDNS/docs/architecture/proxies.md, Law 1). This hook is the only thing standing here,
which is why it has no soft mode.

If the push was rejected as non-fast-forward, reconcile instead:
    git fetch origin $target
    git rebase origin/$target       # rewrites YOUR commits, never theirs
    # then push normally — no force
Expect company on Yggdrasil; another session may have pushed while you worked.
EOF
exit 2
