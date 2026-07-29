#!/usr/bin/env bash
# SessionStart hook — the end-to-end clear-&-refeed ritual, automatic.
#
# Fires when a session starts fresh (source=startup) or is cleared
# (source=clear). Does the two halves the model can't guarantee on its own:
#   1. SYNC  — git fetch, then a guarded fast-forward pull, so the on-disk
#              CLAUDE.md is the latest before anything reads it.
#   2. REFEED — inject the rest of the standing manifest so the fresh session
#              is lossless, not just CLAUDE.md (which Claude Code reloads natively).
#
# Net effect: `/clear` becomes the single end-to-end command. Sync -> clear ->
# refeed, one keystroke, in a real shell. On resume/compact it stays out of the
# way (no pull, no re-inject) so in-progress work isn't disturbed.
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

# --- 2. REFEED (manifest, minus CLAUDE.md which Claude Code reloads itself) --
rev="$(git log -1 --format='%h %ci' -- CLAUDE.md 2>/dev/null || echo unknown)"
read -r -d '' ctx <<EOF || true
REFEED (auto, source=$src). $sync_note. On-disk CLAUDE.md @ $rev is already loaded by Claude Code. To make this session LOSSLESS, read now — in one batch, before other work — the rest of the standing manifest: README.md, docs/ai-cto/context.md, docs/architecture/network-context.md. Together with CLAUDE.md these four are the complete briefing. Do not summarize them back unless asked; just load them and continue. Full protocol: docs/architecture/clear-refeed-protocol.md.
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
