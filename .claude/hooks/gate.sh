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
# Runs the repo's three static checks before any `git commit`:
#   tools/check-docs.py        links + repo-path references resolve; the Bifrost
#                              sweep string is byte-identical across its surfaces
#   tools/check-provenance.py  provenance tags valid; no unstaged R-tier deploy
#                              target; no R/A tag without a verify: route
#   tools/check-doctrine.py    §G's stated sampler values match jury/jury.py
#   tools/sync-briefings.py    every sibling repo's CLAUDE.md Bifrost block matches the
#                              canonical one, and the two briefing tiers agree on glyph
#                              roles. This is the PARALLEL-SESSION check: git conflicts
#                              only on the same file, but the schema lives in a dozen
#                              DIFFERENT files required to agree — so two sessions can
#                              each be green, each push cleanly, and still leave the
#                              portfolio self-contradictory. Siblings not checked out
#                              are skipped, so a green run here is not proof the whole
#                              portfolio is synced — only the part this session can see.
#   tools/check-branch-cap.py  no repo carries more than 9 branches. A `claude/*` ref whose
#                              tip is already reachable from an `archive/*` branch counts as
#                              PENDING (history preserved, only the deletion outstanding —
#                              blocked 403 from here) and is reported, not failed; anything
#                              else over cap fails. A repo whose remote is unreachable is
#                              skipped and named, never silently passed.
#   tools/check-tiers.py       refuses a commit made on `main`, the vetted tier, which moves
#                              only through an approved PR (ADR-008). The mechanical half of
#                              "push to Yggdrasil, never to main" — and session-fixable,
#                              which is the bar for blocking: the run switches branch and
#                              proceeds. The tier GAP it also reports is deliberately
#                              non-blocking, since only the founder can clear that one and a
#                              gate that wedges the repo gets bypassed.
#
# The last two are the same lesson at two scales: check-branch-cap counts the branches
# that accumulate, check-tiers measures the gap that accumulates INSIDE one of them. A
# cap alone would be satisfied by one branch that never merges.
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

# ── Force-push guard (docs/architecture/proxies.md, Law 1 + gap audit) ─────────────
# "Never force-push Yggdrasil or main" (CLAUDE.md §3) was enforced by NOTHING. The agent
# git proxy blocks `--delete` but PERMITS `--force` — proven 2026-08-08 by a successful
# forced update. Both orphan commits; only one was refused. That is a verb-scoped control
# guarding an effect-shaped risk, so the effect gets its own site here.
#
# Scoped by EFFECT, not verb: every spelling that can rewrite a protected ref —
# --force, -f, --force-with-lease, and the `+refspec` form — against Yggdrasil or main.
# A force-push to any OTHER branch is left alone; this guards founder-authored history,
# not every rewrite.
# Quoted text is DATA, not a command: a commit message that discusses force-pushing must
# not trip this. Strip quoted spans first, then scan. A compound `git commit -m '…' &&
# git push --force origin main` still matches, because only the message is quoted.
scan="$(printf '%s' "$cmd" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")"

if printf '%s' "$scan" | grep -Eq '(^|[;&|[:space:]])git([[:space:]]+-[^[:space:]]+)*[[:space:]]+push([[:space:]]|$)'; then
    forced=0
    printf '%s' "$scan" | grep -Eq '[[:space:]](--force([[:space:]]|=|$)|--force-with-lease|-f([[:space:]]|$))' && forced=1
    printf '%s' "$scan" | grep -Eq '[[:space:]]\+[A-Za-z0-9_./-]*(HEAD|Yggdrasil|main)' && forced=1

    if [ "$forced" = 1 ]; then
        # Count non-flag arguments after `push`: <remote> [refspec...]. A refspec means
        # the target is EXPLICIT, so the current branch is irrelevant — `--force origin
        # tmp/scratch` from Yggdrasil must pass. Only when no refspec is given does the
        # push default to the current branch. Over-blocking is not the safe direction:
        # a gate that refuses legitimate work is a gate people switch off.
        args="$(printf '%s' "$scan" \
                | sed -E 's/.*git([[:space:]]+-[^[:space:]]+)*[[:space:]]+push//' \
                | tr ' ' '\n' | grep -v '^-' | grep -v '^$' | tr '\n' ' ')"
        argc="$(printf '%s' "$args" | wc -w)"

        if [ "$argc" -ge 2 ]; then
            # Explicit refspec — block only if it names a protected branch.
            target="$(printf '%s' "$args" | tr ' ' '\n' | tail -n +2 \
                      | grep -oE '(Yggdrasil|main)' | head -1)"
        else
            # No refspec: the push targets the current branch.
            case "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" in
                Yggdrasil|main) target="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" ;;
                *) target="" ;;
            esac
        fi
        if [ -n "$target" ]; then
            cat >&2 <<EOF
COMMIT GATE — blocked. Force-push to \`$target\` refuses here.

A fast-forward can only ADD commits. A forced update REWRITES the ref, orphaning
whatever it passed over — including founder-authored doctrine this session never read.
"A session transcribes doctrine; it does not author it." (CLAUDE.md §3)

The environment will NOT stop you: the agent git proxy blocks --delete but permits
--force (docs/architecture/proxies.md, gap audit). This hook is the only thing standing
here, which is exactly why it does not have a soft mode.

If the push was rejected as non-fast-forward, reconcile instead:
    git fetch origin $target
    git rebase origin/$target       # rewrites YOUR commits, never theirs
    # then push normally — no force
Expect company on Yggdrasil; another session may have pushed while you worked.
EOF
            exit 2
        fi
    fi
fi

# Only gate real commits. `git commit` appearing inside a quoted string (a commit
# MESSAGE that talks about committing, say) is matched too — over-triggering costs
# two seconds; under-triggering costs the invariant.
printf '%s' "$cmd" | grep -Eq '(^|[;&|[:space:]])git[[:space:]]+(-[^[:space:]]+[[:space:]]+)*commit([[:space:]]|$)' || exit 0

fails=""
for check in tools/check-docs.py tools/check-provenance.py tools/check-doctrine.py \
             tools/sync-briefings.py tools/check-branch-cap.py tools/check-tiers.py; do
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
