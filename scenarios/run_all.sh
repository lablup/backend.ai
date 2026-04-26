#!/usr/bin/env bash
# run_all.sh — execute every scenario in order, collecting PASS/FAIL.
#
# Usage:
#   scenarios/run_all.sh                # full run incl. teardown
#   SKIP_TEARDOWN=1 scenarios/run_all.sh  # leave test data behind for inspection
#   ONLY="01 02" scenarios/run_all.sh   # run a subset of scenario numbers

set -uo pipefail

cd "$(dirname "$0")/.."
source scenarios/lib/env.sh
source scenarios/lib/common.sh

SCRIPTS=(
    scenarios/00_setup.sh
    scenarios/01_vfolder_lifecycle.sh
    scenarios/02_session_lifecycle.sh
    scenarios/03_model_card_deploy.sh
    scenarios/04_deployment_revision.sh
    scenarios/05_teardown_verification.sh
    scenarios/06_multi_user_access.sh
    scenarios/07_vfolder_invite_clone.sh
    scenarios/08_cross_project_isolation.sh
    scenarios/09_vfolder_mounted_delete.sh
    scenarios/10_vfolder_cloneable_false.sh
    scenarios/11_vfolder_bulk_ops.sh
    scenarios/12_vfolder_file_io.sh
    scenarios/13_session_exec_logs.sh
    scenarios/14_deployment_endpoint_serve.sh
    scenarios/15_session_concurrency_cap.sh
)

if [[ -n "${ONLY:-}" ]]; then
    FILTERED=()
    for s in "${SCRIPTS[@]}"; do
        for tok in $ONLY; do
            if [[ "$s" == *"/${tok}_"* ]]; then
                FILTERED+=("$s"); break
            fi
        done
    done
    SCRIPTS=("${FILTERED[@]}")
fi

declare -a PASSED FAILED
for script in "${SCRIPTS[@]}"; do
    if bash "$script"; then
        PASSED+=("$script")
    else
        FAILED+=("$script")
    fi
done

if [[ -z "${SKIP_TEARDOWN:-}" ]]; then
    bash scenarios/99_teardown.sh \
        && PASSED+=("scenarios/99_teardown.sh") \
        || FAILED+=("scenarios/99_teardown.sh")
fi

printf '\n%s========================================================================%s\n' "$_C_BOLD" "$_C_RESET"
printf '%s SUMMARY%s\n' "$_C_BOLD" "$_C_RESET"
printf '%s========================================================================%s\n' "$_C_BOLD" "$_C_RESET"
printf '%sPASSED (%d):%s\n' "$_C_GREEN" "${#PASSED[@]}" "$_C_RESET"
for s in "${PASSED[@]}"; do printf '  ✓ %s\n' "$s"; done

if (( ${#FAILED[@]} > 0 )); then
    printf '%sFAILED (%d):%s\n' "$_C_RED" "${#FAILED[@]}" "$_C_RESET"
    for s in "${FAILED[@]}"; do printf '  ✗ %s\n' "$s"; done
    exit 1
fi
printf '%sAll scenarios passed.%s\n' "$_C_GREEN" "$_C_RESET"
