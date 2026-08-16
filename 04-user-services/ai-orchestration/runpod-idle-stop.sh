#!/bin/bash
# Deploys to: ~/llm-router/runpod-idle-stop.sh  (chmod +x)
# Scheduled via: crontab -e  →  */5 * * * * /home/USER/llm-router/runpod-idle-stop.sh
#
# Golden-rule safety net (CLAUDE.md 04-user-services/ai-orchestration §"Offload heavy
# reasoning to a rented GPU"): a rented pod left running drains the prepaid balance
# whether or not anyone remembers to hit stop. This makes "always hit stop" a cron
# job instead of a thing a human has to remember. See REMEDIATION-BOARD.md Track 6
# "Exception (2026-08-16)" for why this GPU-rental piece exists ahead of that track's
# usual deferral.
#
# What it does: polls the RunPod pod's GPU utilization over Tailscale (SSH). Below
# IDLE_THRESHOLD_PCT for CONSECUTIVE_IDLE_CHECKS runs in a row, it stops the pod via
# the RunPod API. Utilization above threshold resets the counter. If the pod is
# already stopped/unreachable, it exits quietly — nothing to do.
#
# Requires on the t630: ssh key auth to the pod (RunPod's default `root@<host>`),
# curl. Env vars come from ~/llm-router/.env (see .env.example):
#   RUNPOD_API_KEY, RUNPOD_POD_ID, TAILSCALE_GPU_HOST
#
# Install:
#   cp 04-user-services/ai-orchestration/runpod-idle-stop.sh ~/llm-router/runpod-idle-stop.sh
#   chmod +x ~/llm-router/runpod-idle-stop.sh
#   crontab -e   →   add:  */5 * * * * /home/USER/llm-router/runpod-idle-stop.sh

set -euo pipefail

ENV_FILE="${ENV_FILE:-$HOME/llm-router/.env}"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

: "${RUNPOD_API_KEY:?set in ~/llm-router/.env}"
: "${RUNPOD_POD_ID:?set in ~/llm-router/.env}"
: "${TAILSCALE_GPU_HOST:?set in ~/llm-router/.env}"

IDLE_THRESHOLD_PCT="${IDLE_THRESHOLD_PCT:-5}"
CONSECUTIVE_IDLE_CHECKS="${CONSECUTIVE_IDLE_CHECKS:-3}"   # 3 checks * 5min cron = 15min idle
STATE_FILE="${STATE_FILE:-$HOME/.cache/runpod-idle-stop.count}"
mkdir -p "$(dirname "$STATE_FILE")"

util=$(ssh -o ConnectTimeout=5 -o BatchMode=yes "root@${TAILSCALE_GPU_HOST}" \
  "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits" 2>/dev/null | head -1) || {
  # Pod unreachable — already stopped, or not up yet. Nothing to enforce.
  rm -f "$STATE_FILE"
  exit 0
}

util=${util:-0}
count=0
[ -f "$STATE_FILE" ] && count=$(cat "$STATE_FILE")

if [ "$util" -lt "$IDLE_THRESHOLD_PCT" ]; then
  count=$((count + 1))
else
  count=0
fi
echo "$count" > "$STATE_FILE"

if [ "$count" -ge "$CONSECUTIVE_IDLE_CHECKS" ]; then
  curl -s -X POST "https://api.runpod.io/graphql?api_key=${RUNPOD_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"mutation { podStop(input: {podId: \\\"${RUNPOD_POD_ID}\\\"}) { id desiredStatus } }\"}" \
    > /dev/null
  rm -f "$STATE_FILE"
fi
