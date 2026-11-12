#!/usr/bin/env bash
# factory.sh: the software factory loop for the racetrack queue.
#
# A bounded loop over the queue in docs/ai-cto/fleet/racetrack/factory-queue.tsv. Each pass checks the
# gates, the running agents and the token budget, then picks the next milestone that is not done.
#
# A shell cannot launch an Agent-tool subagent; only the session can. So the loop HANDS OFF: it writes
# the milestone's task file and exits 4, and the session launches one agent for it. When that agent
# finishes, the session records it:   bash tools/factory.sh --finish ID TOKENS
# and the loop continues from the next milestone.
#
# Stop conditions (every one exits non-zero, with its reason on stdout):
#   1  a gate is red (check-all --quick fails)           stop; fix the gate
#   2  an agent is still running (the ledger has a launch with no finish)
#   3  the token budget is spent
#   0  the queue is empty: every milestone is done
#   4  hand-off: the session launches the next milestone's agent
#
#   bash tools/factory.sh                   run the loop from where it left off
#   bash tools/factory.sh --finish ID TOK   record a finished milestone and its tokens, then resume
#
# Budget: FACTORY_BUDGET_TOKENS (default 2,400,000, the $5 lease at the output-rate estimate).
# Iteration cap: FACTORY_MAX_PASSES (default 10). The cap is a bound on runaway, never a goal.
set -u
cd "$(dirname "$0")/.." || { echo "STOP: cannot enter the repo root"; exit 1; }

# Budget precedence: the env var, then the budget file (set by the founder, local and gitignored), then 2,400,000.
BUDGET="${FACTORY_BUDGET_TOKENS:-}"
if [ -z "$BUDGET" ] && [ -f .claude/.factory-budget ]; then BUDGET="$(tr -d '[:space:]' < .claude/.factory-budget)"; fi
BUDGET="${BUDGET:-2400000}"
MAX_PASSES="${FACTORY_MAX_PASSES:-10}"
TASKS=".claude/factory-tasks"  # gitignored: the loop's own output must not dirty the tree it checks

if [ "${1:-}" = "--finish" ]; then
  [ $# -eq 3 ] || { echo "STOP: --finish takes ID and TOKENS"; exit 1; }
  python3 tools/matrix.py observe.factory done "$2" "$3" || { echo "STOP: could not record $2"; exit 1; }
  echo "recorded $2 ($3 tokens)"
  shift 3
fi

pass=0
while [ "$pass" -lt "$MAX_PASSES" ]; do
  pass=$((pass + 1))

  # 2. Agents first: no new milestone starts while a launched agent has no recorded finish.
  # (Checked before the gates, so a running agent is reported as itself, not as a red gate.)
  if ! python3 tools/matrix.py observe.agents check >/dev/null 2>&1; then
    echo "STOP 2: an agent is still running. Record its finish, then rerun."
    exit 2
  fi

  # 1. Gates: a red gate stops the factory; it does not pass a bad result on.
  if ! bash tools/check-all.sh --quick >/dev/null 2>&1; then
    echo "STOP 1: a gate is red. Run: bash tools/check-all.sh --quick"
    exit 1
  fi

  # 3. Budget: stop before the next launch once the token budget is spent.
  spent="$(python3 tools/matrix.py observe.factory spent)"
  if [ "$spent" -ge "$BUDGET" ]; then
    echo "STOP 3: budget spent ($spent of $BUDGET tokens)."
    exit 3
  fi

  # 0. Queue: the next milestone not yet done. Empty means the factory is finished.
  next="$(python3 tools/matrix.py observe.factory next)"
  if [ -z "$next" ]; then
    echo "DONE 0: every queued milestone is done; $spent tokens spent."
    exit 0
  fi

  # 4. Hand-off: write the task for the session, then stop so the session can launch its agent.
  mkdir -p "$TASKS"
  line="$(awk -F'\t' -v id="$next" '$1 == id' docs/ai-cto/fleet/racetrack/factory-queue.tsv)"
  file="$(printf '%s' "$line" | cut -f2)"
  question="$(printf '%s' "$line" | cut -f3-)"
  printf 'Milestone %s\nRead: %s\nQuestion: %s\nWrite: %s/%s.md (defects, file and line, Notes as plain paragraphs)\n' \
    "$next" "$file" "$question" "$TASKS" "$next" > "$TASKS/$next.task"
  echo "HAND-OFF 4: milestone $next is ready. The session launches one agent for $TASKS/$next.task,"
  echo "then records it with: bash tools/factory.sh --finish $next TOKENS"
  exit 4
done

echo "STOP: pass cap reached ($MAX_PASSES passes) without a hand-off. Raise FACTORY_MAX_PASSES only if this is expected."
exit 5
