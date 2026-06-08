#!/usr/bin/env bash
# Stand up the Odin supervisor's venv in one shot. Idempotent — safe to re-run.
# Deploys to ~/llm-router/langgraph-router/ on the t630; run it from this folder:
#   bash setup.sh
#
# It does NOT deploy the gateway (that's the LiteLLM compose, one level up) and it does
# NOT need a live front door — it just builds the venv and proves the safety logic.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
VENV=".venv"

echo "==> Odin supervisor setup (in $(pwd))"

# 1. The deterministic safety logic runs on the stdlib alone — prove it FIRST, no venv
#    needed. If this fails, stop before installing anything.
echo "==> Self-tests (stdlib only — Heimdall, the Warden, Loki's binding, Frigg, the Hoard, RAG):"
"$PY" supervisor.py --selftest
"$PY" frigg.py --selftest
"$PY" hoard.py  --selftest
"$PY" tools.py  --selftest
"$PY" rag.py    --selftest

# 2. Build the venv and install the graph deps (only needed to actually RUN the graph).
if [ ! -d "$VENV" ]; then
  echo "==> Creating venv ($VENV)"
  "$PY" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
echo "==> Installing requirements"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo
echo "==> Done. The host is mustered. Next:"
echo "    1. Make sure the gateway is up:  curl -s http://ai.home.lan:4040/health"
echo "    2. Set secrets in ~/llm-router/.env (LITELLM_MASTER_KEY, etc.)"
echo "    3. (optional) Build Mímir's well:  python3 rag.py --build ../.. --out mimir.json"
echo "       then export LLM_ROUTER_INDEX=\$(pwd)/mimir.json"
echo "    4. Ride out:  ./odin \"research X, then write a config diff\""
echo "       (summon Loki: LOKI=1 ./odin \"...\";  arm the Hoard: LLM_ROUTER_BUDGET_USD=2 ./odin \"...\")"
