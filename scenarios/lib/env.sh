#!/usr/bin/env bash
# Shared environment for scenario scripts.
# Source from each scenario: `source "$(dirname "$0")/lib/env.sh"`.

# Endpoints
export BAI_ENDPOINT="${BAI_ENDPOINT:-http://127.0.0.1:8090}"
export BAI_ENDPOINT_TYPE="${BAI_ENDPOINT_TYPE:-session}"

# Admin credentials (from fixtures/manager/example-users.json)
export ADMIN_EMAIL="${ADMIN_EMAIL:-admin@lablup.com}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-wJalrXUt}"

# Test user/project names — prefixed to avoid collision
export SCENARIO_PREFIX="${SCENARIO_PREFIX:-scn}"
export TEST_USER_A_EMAIL="${SCENARIO_PREFIX}-userA@scenario.local"
export TEST_USER_A_NAME="${SCENARIO_PREFIX}-userA"
export TEST_USER_A_PASSWORD="ScenarioPassA1!"
export TEST_USER_B_EMAIL="${SCENARIO_PREFIX}-userB@scenario.local"
export TEST_USER_B_NAME="${SCENARIO_PREFIX}-userB"
export TEST_USER_B_PASSWORD="ScenarioPassB1!"

export TEST_PROJECT_A_NAME="${SCENARIO_PREFIX}-projectA"
export TEST_PROJECT_B_NAME="${SCENARIO_PREFIX}-projectB"

# Domain / scaling group / hosts / policies
export TEST_DOMAIN="${TEST_DOMAIN:-default}"
export TEST_RESOURCE_GROUP="${TEST_RESOURCE_GROUP:-default}"
export TEST_VFOLDER_HOST="${TEST_VFOLDER_HOST:-local:volume1}"
export TEST_KEYPAIR_RESOURCE_POLICY="${TEST_KEYPAIR_RESOURCE_POLICY:-default}"
export TEST_USER_RESOURCE_POLICY="${TEST_USER_RESOURCE_POLICY:-default}"
export TEST_PROJECT_RESOURCE_POLICY="${TEST_PROJECT_RESOURCE_POLICY:-default}"

# Default image (aarch64). Override for x86_64 hosts.
# Find current ID with: ./bai admin image search --architecture aarch64 --name-contains "python:3.12-ubuntu24.04-arm64"
export TEST_IMAGE_NAME="${TEST_IMAGE_NAME:-cr.backend.ai/stable/python:3.12-ubuntu24.04-arm64}"

# Working/state dir for cross-script artifacts (uuid lookups, etc.)
export SCENARIO_STATE_DIR="${SCENARIO_STATE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.state}"
mkdir -p "$SCENARIO_STATE_DIR"

# Temp dir for upload/download artifacts
export SCENARIO_TMP_DIR="${SCENARIO_TMP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.tmp}"
mkdir -p "$SCENARIO_TMP_DIR"
