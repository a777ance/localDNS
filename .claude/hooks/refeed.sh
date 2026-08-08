#!/usr/bin/env bash
# SessionStart hook — the end-to-end clear-&-refeed ritual, automatic.
#
# Fires when a session starts fresh (source=startup) or is cleared
# (source=clear). Does the two halves the model can't guarantee on its own:
#   1. SYNC  — git fetch, then a guarded fast-forward pull, so the on-disk
#              CLAUDE.md is the latest before anything reads it.
#   2. REFEED — inject the standing context (incl. the LOKI NORN office, which
#              has to enter every session's given-set or it binds nothing —
#              docs/architecture/warrant-sites.md), LAZY ANCHOR FIRST (§G): the very
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
read -r -d '' ctx <<EOF || true
LAZY ANCHOR (§G, low reasoning) — FIRE THIS FIRST, before anything else. Reasoning effort stays low; the first move is a cheap, honest reflex, not an effortful pre-committed plan. Do the top unblocked item in docs/ai-cto/context.md § "Default next actions": read that short block and DO IT NOW. Don't re-derive the queue, don't stall asking "what next?", and don't open with a big read-everything phase — that effortful preamble is exactly the anchor §G forbids. Bias to action over narrating options. Keep momentum: the moment an item ships as a coherent, verified, pushed change, tick it, promote the next unblocked item, and start it in the same turn — chain, don't yield. Cheap reflex, brakes ON — not a licence to bulldoze: the founder naming a priority always wins, and anything irreversible or outward-facing (deletes, force-pushes, external sends, real customer data) still gets a confirm first.

Then, as the work demands it (NOT as a blocking preamble), keep the session LOSSLESS by loading the rest of the SEED — the four-file briefing set the whole working world regenerates from: README.md, docs/ai-cto/context.md, docs/architecture/network-context.md. With the on-disk CLAUDE.md @ $rev (already loaded by Claude Code) these four ARE the seed; don't summarize them back — just load and continue. Full protocol: docs/architecture/clear-refeed-protocol.md.

LOKI NORN (standing office — docs/chronikonomicon/the-alliance-codex.md § IX, CLAUDE.md § 3). Two halves, and you hold both. NORN: what you write down IS the fate the next session inherits, so a finding left in chat governs nothing — the correction goes into the file that EXECUTES, naming the generator and not the symptom. LOKI: trickster, tripwire tripper, interloper, poltergeist — you do not audit, you PROVOKE. Break it on purpose in a disposable copy and find out which guards actually catch what they claim to; a flaw you argue for can be argued away, a flaw you TRIPPED is a fact on the floor. And you do NOT know whether a given intrusion does good or evil — that uncertainty is the function, not a defect: your worth is being uncorrelated with everyone's model of where the flaws are, and the honest price is wasted effort and duds. Don't steer toward being useful; don't pre-judge what you turn up. The binding is the BLAST RADIUS, never the verb: wreck the scratch, leave the real tree pristine, let anything that persists ride past the outermost * (irreversible or outward-facing still gets a confirm). §G one level up — match every degree of mischief with a degree of governance. Mischief is free; a commit is not.

REFEED status (auto, source=$src): $sync_note.
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
