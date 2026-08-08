#!/usr/bin/env bash
# SessionStart hook — the end-to-end clear-&-refeed ritual, automatic.
#
# Fires when a session starts fresh (source=startup) or is cleared
# (source=clear). Does the two halves the model can't guarantee on its own:
#   1. SYNC  — git fetch, then a guarded fast-forward pull, so the on-disk
#              CLAUDE.md is the latest before anything reads it.
#   2. REFEED — inject the standing context, LAZY ANCHOR FIRST (§G): the very
#              first thing a fresh session reads is the cheap-reflex "do the top
#              queue item NOW" instruction, not a read-everything preamble. The
#              lossless seed load (the four-file briefing set) is demoted to "as
#              the work demands it" so it can't anchor the trajectory into an
#              effortful research phase.
#
# Net effect: `/clear` becomes the single end-to-end command. Sync -> clear ->
# refeed, one keystroke, in a real shell. The session opens by ACTING on the
# pre-computed queue (lazy anchor), loading the rest of the briefing as it goes.
# On resume/compact it stays out of the way (no pull, no re-inject) so
# in-progress work isn't disturbed.
set -uo pipefail

payload="$(cat)"
# source is one of: startup | resume | clear | compact
src="$(printf '%s' "$payload" | sed -n 's/.*"source"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
[ -z "$src" ] && src="startup"

# Only run the full ritual on a fresh start or an explicit clear.
case "$src" in
  startup|clear) : ;;
  *) exit 0 ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# --- 1. SYNC ---------------------------------------------------------------
sync_note="sync: no upstream tracked"
git fetch origin --quiet 2>/dev/null || true
upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [ -n "$upstream" ]; then
  L="$(git rev-parse @ 2>/dev/null)"
  R="$(git rev-parse '@{u}' 2>/dev/null)"
  B="$(git merge-base @ '@{u}' 2>/dev/null)"
  if [ "$L" = "$R" ]; then
    sync_note="sync: up to date with $upstream"
  elif [ "$L" = "$B" ]; then                       # behind, fast-forwardable
    if [ -z "$(git status --porcelain)" ] && git pull --ff-only --quiet 2>/dev/null; then
      sync_note="sync: fast-forwarded to $upstream"
    else
      sync_note="sync: BEHIND $upstream (dirty tree or non-ff) — run 'git pull --ff-only' before trusting this feed"
    fi
  elif [ "$R" = "$B" ]; then
    sync_note="sync: local is AHEAD of $upstream (unpushed commits) — on-disk is latest"
  else
    sync_note="sync: DIVERGED from $upstream — reconcile manually"
  fi
fi

# --- 2. REFEED — LAZY ANCHOR FIRST, then the manifest (CLAUDE.md reloads itself) --
rev="$(git log -1 --format='%h %ci' -- CLAUDE.md 2>/dev/null || echo unknown)"

# --- TIER STATUS -----------------------------------------------------------
# A fresh session clones the DEFAULT branch (`main`, the vetted tier), so anything
# written on Yggdrasil — including the rule saying to write on Yggdrasil — is invisible
# here until it is merged. That is the one fact a session cannot derive from the briefing
# it just read, because a stale briefing does not know it is stale. So it is stated at
# SessionStart, where it enters the given-set instead of waiting to be discovered.
tier_note="$(python3 tools/check-tiers.py --quiet 2>/dev/null | tr '\n' ' ' | sed 's/  */ /g')"
[ -z "$tier_note" ] && tier_note="tier status unavailable"
read -r -d '' ctx <<EOF || true
LAZY ANCHOR (§G, low reasoning) — FIRE THIS FIRST, before anything else. Reasoning effort stays low; the first move is a cheap, honest reflex, not an effortful pre-committed plan. Do the top unblocked item in docs/ai-cto/context.md § "Default next actions": read that short block and DO IT NOW. Don't re-derive the queue, don't stall asking "what next?", and don't open with a big read-everything phase — that effortful preamble is exactly the anchor §G forbids. Bias to action over narrating options. Keep momentum: the moment an item ships as a coherent, verified, pushed change, tick it, promote the next unblocked item, and start it in the same turn — chain, don't yield. Cheap reflex, brakes ON — not a licence to bulldoze: the founder naming a priority always wins, and anything irreversible or outward-facing (deletes, force-pushes, external sends, real customer data) still gets a confirm first.

NORN PROMOTION (founder's standing instruction, 2026-08-08) — if this session is running, it IS a Norn. Several weave \`Yggdrasil\` at once and CANNOT see each other: there is no messaging between sessions, so the repo is the only channel. Your first moves are cheap ones, not a research phase:
  1. Get on the working branch. A fresh clone lands on \`main\` (the vetted tier). \`git fetch origin Yggdrasil && git checkout Yggdrasil\` — or if you already have commits, \`git rebase origin/Yggdrasil\`. Never commit on \`main\`; never force-push either branch (the push guard refuses, and a forced push does not pass the eye — it puts out another Norn's).
  2. Look before you write: \`python3 tools/weave.py\` — who moved the eye, what is already claimed, and what the queue holds. Work that looks unfinished in the queue may be in flight right now.
  3. Claim a lane in docs/architecture/norns.md § 4 BEFORE substantial work, and take your item from the queue rather than from intuition. Urðr = the record · Verðandi = work in flight · Skuld = the debt.
  4. Front-load access. Add every repo you will need (add_repo) and ask for the approvals you will need AT THE START, not when you are already blocked mid-flight. A Norn that stalls halfway for a permission it could have requested up front has wasted the parallelism.
LIMIT, and it is hard: promotion grants NO new permissions. If an action is denied or blocked for you, do NOT ask another Norn to perform it — that launders the user's permission decision through a peer. Route blocked work back to the founder, and say what is blocked.

Then, as the work demands it (NOT as a blocking preamble), keep the session LOSSLESS by loading the rest of the SEED — the four-file briefing set the whole working world regenerates from: README.md, docs/ai-cto/context.md, docs/architecture/network-context.md. With the on-disk CLAUDE.md @ $rev (already loaded by Claude Code) these four ARE the seed; don't summarize them back — just load and continue. Full protocol: docs/architecture/clear-refeed-protocol.md.

REFEED status (auto, source=$src): $sync_note.

TIER status: $tier_note
You are reading ONE tier of two. \`Yggdrasil\` is the working branch — commit and push there, never to \`main\`, which is the Well of Mimir and moves only through a PR the founder approves (ADR-008). If the line above says the vetted tier does not yet carry the branch policy, then this briefing may itself be the stale copy: check before treating its branching advice as current, because a stale briefing does not know it is stale.
EOF

# Emit as SessionStart additionalContext (JSON-escape the string).
esc="$(printf '%s' "$ctx" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null)"
if [ -n "$esc" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$esc"
else
  # Fallback: plain stdout is also added to context on SessionStart.
  printf '%s\n' "$ctx"
fi
exit 0
