#!/usr/bin/env bash
# Single entry point: lint, unit tests, repo checks. Exits 1 if ANY step fails.
# Lint is not optional: a missing ruff is a failure, not a skip.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
fail=0
step() {
    echo "== $1"
    shift
    if "$@"; then echo "   ok"; else echo "   FAILED: $*"; fail=1; fi
}
step "ruff lint (repo config)" ruff check --config ruff.toml .
step "unit tests" python3 -m unittest discover -s tests
for check in tools/check-docs.py tools/check-doctrine.py tools/check-provenance.py \
             tools/check-debt.py tools/sync-briefings.py; do
    step "$check" python3 "$check"
done
if [ "$fail" -eq 0 ]; then echo "VERIFY PASSED"; else echo "VERIFY FAILED"; exit 1; fi
