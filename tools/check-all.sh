#!/usr/bin/env bash
# check-all.sh: the one entry point for "is this repo healthy, and may I run?".
#
# Runs, in order, every step the preflight in docs/ai-cto/fleet/racetrack/RULES.md asks for, plus every
# static gate. FAIL CLOSED: a missing script, a non-zero exit, or an unreadable result fails the whole run.
# Exit 0 only when every step passes. Nothing is skipped silently.
#
#   bash tools/check-all.sh            run everything, print one line per step, then a summary
#   bash tools/check-all.sh --quick    the repo state, the probes and the fast gates only
#
# Standard library and bash only. Writes nothing except the summary on stdout.
set -u
cd "$(dirname "$0")/.." || { echo "FAILED: cannot enter the repo root"; exit 1; }

QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1

FAILS=0
PASSES=0
STEPS=()

step() {
  # step NAME COMMAND...  : run one step, record it, fail closed on any non-zero exit.
  local name="$1"; shift
  local out
  out=$("$@" 2>&1)
  local code=$?
  if [ "$code" -eq 0 ]; then
    PASSES=$((PASSES + 1))
    printf 'ok      %s\n' "$name"
  else
    FAILS=$((FAILS + 1))
    printf 'FAILED  %s (exit %s)\n' "$name" "$code"
    printf '%s\n' "$out" | tail -n 6 | sed 's/^/        /'
  fi
  STEPS+=("$name")
}

need() {
  # need PATH : a required file must exist, or the run fails closed.
  if [ -e "$1" ]; then
    PASSES=$((PASSES + 1))
    printf 'ok      present %s\n' "$1"
  else
    FAILS=$((FAILS + 1))
    printf 'FAILED  missing %s\n' "$1"
  fi
}

echo "== repo state"
step "clean working tree" bash -c 'test -z "$(git status --porcelain)"'
step "leader matches origin/leader" bash -c 'test "$(git rev-parse HEAD)" = "$(git ls-remote origin refs/heads/leader | cut -f1)"'

echo "== required files"
for f in CLAUDE.md .claude/cardinal-map.json .claude/hooks/cardinal.py .claude/hooks/decide-act.py \
         .claude/hooks/gate.sh tools/matrix.py tools/racetrack.py docs/ai-cto/fleet/racetrack/RULES.md; do
  need "$f"
done

echo "== matrix probes (lane 0)"
step "orient.probe" python3 tools/matrix.py orient.probe
step "decide.probe" python3 tools/matrix.py decide.probe
step "observe.probe push" python3 tools/matrix.py observe.probe push

echo "== static gates"
step "check-cardinal" python3 tools/check-cardinal.py
step "check-superfleet" python3 tools/check-superfleet.py
step "check-decisions" python3 tools/check-decisions.py
step "check-docs" python3 tools/check-docs.py
step "check-provenance" python3 tools/check-provenance.py
step "check-registers" python3 tools/check-registers.py
step "racetrack arena self-test" python3 tools/racetrack.py --selftest
step "no agent running (agent ledger)" python3 tools/matrix.py observe.agents check

if [ "$QUICK" -eq 0 ]; then
  echo "== slower gates"
  step "check-matrix (end to end)" python3 tools/check-matrix.py
  step "check-stop-hook" python3 tools/check-stop-hook.py
  step "check-doctrine" python3 tools/check-doctrine.py
  step "check-statements" python3 tools/check-statements.py
fi

echo "== summary"
echo "passed $PASSES · failed $FAILS · steps $((PASSES + FAILS))"
if [ "$FAILS" -ne 0 ]; then
  echo "FAILED: $FAILS step(s) failed. Fix the cause, then rerun. Nothing is skipped."
  exit 1
fi
echo "ok: every step passed."
exit 0
