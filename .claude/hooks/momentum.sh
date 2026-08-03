#!/usr/bin/env bash
# Stop hook — guarded auto-continue ("momentum") loop.
#
# OFF BY DEFAULT. Inert unless explicitly armed for a session:
#     touch .claude/.momentum-on      # arm  (start a hands-off burst)
#     rm    .claude/.momentum-on      # kill (stop immediately)
#
# When armed, this fires each time the agent tries to end its turn and, while
# there is real momentum, forces it to continue the Default-next-actions queue
# instead of yielding. It is designed so it CANNOT run away:
#
#   * Opt-in            — does nothing unless .claude/.momentum-on exists.
#   * Hard cap          — stops after MAX auto-continues, no matter what.
#   * No-progress stop  — if the last turn shipped no new commit (HEAD didn't
#                         move), there's nothing to sustain, so it yields.
#   * Self-disarming    — on any stop condition it removes the arm file, so the
#                         loop never silently re-engages; you re-arm to run again.
#   * Agent escape hatch— the injected reason tells the agent to `rm` the arm
#                         file itself the moment it's blocked / awaiting input /
#                         out of queue, so it's never trapped from asking you.
#
# Irreversible or outward-facing actions still require a confirm first — the loop
# sustains momentum, it does not override that rule (see refeed.sh lazy anchor).
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

ARM=".claude/.momentum-on"
STATE=".claude/.momentum-state"
MAX=10

# Inert unless armed.
[ -f "$ARM" ] || exit 0

allow_stop() { rm -f "$ARM" "$STATE"; exit 0; }   # disarm and let the turn end

count=0; lastsha=""
[ -f "$STATE" ] && read -r count lastsha < "$STATE" 2>/dev/null || true
case "$count" in ''|*[!0-9]*) count=0 ;; esac

head="$(git rev-parse HEAD 2>/dev/null || echo none)"

# Stop condition 1: hard iteration cap.
[ "$count" -ge "$MAX" ] && allow_stop
# Stop condition 2: no progress since the last continue (nothing shipped).
[ -n "$lastsha" ] && [ "$head" = "$lastsha" ] && allow_stop

# Otherwise there IS momentum: record state and block the stop (force continue).
count=$((count + 1))
printf '%s %s\n' "$count" "$head" > "$STATE"

reason="AUTO-MOMENTUM ${count}/${MAX}: keep going — do the next unblocked item in docs/ai-cto/context.md section \"Default next actions\", ship it as a verified, pushed change, then continue. STOP the loop YOURSELF the instant you are blocked, awaiting the founder, or the queue is empty, by running: rm -f ${ARM}. Anything irreversible or outward-facing (deletes, force-pushes, external sends, real customer data) still needs a confirm first."

esc="$(printf '%s' "$reason" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null)"
[ -z "$esc" ] && allow_stop   # if we can't build valid JSON, fail safe → stop
printf '{"decision":"block","reason":%s}\n' "$esc"
exit 0
