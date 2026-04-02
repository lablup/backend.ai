#!/bin/bash
# Run all E2E model store scenarios in order.
#
# Usage: bash scripts/e2e-model-store/run-all.sh
#
# Prerequisites:
#   - Local halfstack running (DB, Redis, etcd)
#   - Manager server running (./dev start mgr)
#   - At least one model VFolder and image available
#   - ./bai login completed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

run_scenario() {
    local script="$1"
    local name
    name=$(basename "$script")
    echo ""
    echo "================================================================"
    echo "  Running: $name"
    echo "================================================================"
    if bash "$script"; then
        echo "  >> $name: OK"
    else
        echo "  >> $name: FAILED (exit code $?)"
        exit 1
    fi
}

echo "=== Model Store E2E Test Suite ==="

run_scenario "$SCRIPT_DIR/01-setup-presets.sh"
run_scenario "$SCRIPT_DIR/02-deploy-manual.sh"
run_scenario "$SCRIPT_DIR/03-deploy-with-preset.sh"
run_scenario "$SCRIPT_DIR/04-deploy-preset-override.sh"
run_scenario "$SCRIPT_DIR/05-add-revision-with-preset.sh"
run_scenario "$SCRIPT_DIR/06-revision-lifecycle.sh"
run_scenario "$SCRIPT_DIR/07-route-health-lifecycle.sh"

echo ""
echo "================================================================"
echo "  Cleanup"
echo "================================================================"
run_scenario "$SCRIPT_DIR/99-cleanup.sh"

echo ""
echo "=== All E2E scenarios passed ==="
