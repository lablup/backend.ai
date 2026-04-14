#!/usr/bin/env python3
"""
Rolling Update E2E test with manager log capture (replica count = 3).

Creates a deployment with 3 replicas, waits for RUNNING, adds revision v2,
activates v2, and captures manager logs filtered for rolling-update-related entries.

Usage:
    ./py scripts/test_rolling_update_e2e_with_logs.py
"""
import base64
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import yarl
from dateutil.tz import tzutc

from ai.backend.client.auth import generate_signature

API_ENDPOINT = yarl.URL("http://127.0.0.1:8091")
API_VERSION = "v8.20240915"
ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HASH_TYPE = "sha256"

# ── Target IDs ──
PROJECT_ID = "2de2b969-1d04-48a6-af16-0bc8adb3c831"
DOMAIN_NAME = "default"
IMAGE_ID = "4423c78d-b698-4388-b7c8-44fc52f61be1"
MODEL_VFOLDER_ID = "fb0389a96a1945bc8fb0da6e69808dea"  # rolling-e2e-model-user (user ownership)
RESOURCE_GROUP = "default"

DESIRED_REPLICA_COUNT = 3
POLL_INTERVAL_SECONDS = 3
POLL_TIMEOUT_SECONDS = 600

# ── Log capture config ──
TMUX_SESSION = "0"
TMUX_MANAGER_WINDOW = "1"
LOG_FILE = Path("/tmp/rolling_update_manager_logs.txt")
FILTERED_LOG_FILE = Path("/tmp/rolling_update_filtered_logs.txt")

# Keywords to filter from manager logs
LOG_FILTER_PATTERNS = [
    r"rolling",
    r"deploy",
    r"revision",
    r"route",
    r"routing",
    r"endpoint",
    r"sub_step",
    r"lifecycle",
    r"sokovan",
    r"strategy",
    r"surge",
    r"drain",
    r"provision",
    r"activate",
    r"swap",
    r"current_revision",
    r"deploying_revision",
    r"DEPLOYING",
    r"RUNNING",
    r"HEALTHY",
    r"UNHEALTHY",
    r"PROVISIONING",
    r"COMPLETED",
]
LOG_FILTER_REGEX = re.compile("|".join(LOG_FILTER_PATTERNS), re.IGNORECASE)

# Exclude noisy lines
LOG_EXCLUDE_PATTERNS = [
    r"Message sent to stream",
    r"Event task .+ produced event",
    r"redis_queue",
]
LOG_EXCLUDE_REGEX = re.compile("|".join(LOG_EXCLUDE_PATTERNS), re.IGNORECASE)


# ── GraphQL Queries ──

CREATE_DEPLOYMENT_MUTATION = """
mutation CreateDeployment($input: CreateDeploymentInput!) {
  createModelDeployment(input: $input) {
    deployment {
      id
      metadata {
        name
        status
      }
      revision {
        id
        name
      }
      defaultDeploymentStrategy {
        type
      }
      replicaState {
        desiredReplicaCount
      }
    }
  }
}
"""

GET_DEPLOYMENT_QUERY = """
query GetDeployment($id: ID!) {
  deployment(id: $id) {
    id
    metadata {
      name
      status
    }
    revision {
      id
      name
    }
    replicaState {
      desiredReplicaCount
    }
  }
}
"""

ADD_REVISION_MUTATION = """
mutation AddRevision($input: AddRevisionInput!) {
  addModelRevision(input: $input) {
    revision {
      id
      name
    }
  }
}
"""

ACTIVATE_REVISION_MUTATION = """
mutation ActivateRevision($input: ActivateRevisionInput!) {
  activateDeploymentRevision(input: $input) {
    deployment {
      id
      metadata {
        status
      }
      revision {
        id
        name
      }
    }
    previousRevisionId
    activatedRevisionId
  }
}
"""

SEARCH_ROUTES_QUERY = """
query SearchRoutes($deploymentId: ID!, $first: Int, $offset: Int) {
  routes(deploymentId: $deploymentId, first: $first, offset: $offset) {
    edges {
      node {
        id
        status
        trafficStatus
        trafficRatio
        revisionId
        sessionId
        createdAt
      }
    }
    count
  }
}
"""


def make_headers():
    method = "POST"
    rel_url = "/admin/gql/strawberry"
    date = datetime.now(tzutc())
    content_type = "application/json"
    hdrs, _ = generate_signature(
        method=method,
        version=API_VERSION,
        endpoint=API_ENDPOINT,
        date=date,
        rel_url=rel_url,
        content_type=content_type,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        hash_type=HASH_TYPE,
    )
    return {
        "Content-Type": content_type,
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }


def gql_request(query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    response = requests.post(
        str(API_ENDPOINT / "admin/gql/strawberry"),
        headers=make_headers(),
        json=body,
    )
    result = response.json()
    if result.get("errors"):
        print(f"  GraphQL Errors: {json.dumps(result['errors'], indent=2)}")
    return result


def decode_global_id(global_id):
    return base64.b64decode(global_id).decode().split(":")[1]


def _safe_decode_id(value):
    """Decode a relay Global ID or return raw UUID as-is."""
    if not value or value == "N/A":
        return value or "N/A"
    try:
        return base64.b64decode(value).decode().split(":")[1]
    except Exception:
        return str(value)


def make_revision_input(name, vfolder_id):
    return {
        "name": name,
        "clusterConfig": {
            "mode": "SINGLE_NODE",
            "size": 1,
        },
        "resourceConfig": {
            "resourceGroup": {"name": RESOURCE_GROUP},
            "resourceSlots": {
                "entries": [
                    {"resourceType": "cpu", "quantity": "1"},
                    {"resourceType": "mem", "quantity": "1073741824"},
                ],
            },
        },
        "image": {
            "id": IMAGE_ID,
        },
        "modelRuntimeConfig": {
            "runtimeVariant": "custom",
        },
        "modelMountConfig": {
            "vfolderId": vfolder_id,
            "mountDestination": "/models",
            "definitionPath": "model-definition.yaml",
        },
        "extraMounts": [],
    }


# ── Log capture helpers ──

def start_log_capture():
    """Start capturing manager tmux pane output to a file."""
    LOG_FILE.unlink(missing_ok=True)
    FILTERED_LOG_FILE.unlink(missing_ok=True)
    subprocess.run(
        [
            "tmux", "pipe-pane", "-t",
            f"{TMUX_SESSION}:{TMUX_MANAGER_WINDOW}",
            f"cat >> {LOG_FILE}",
        ],
        check=True,
    )
    print(f"  Log capture started → {LOG_FILE}")


def stop_log_capture():
    """Stop capturing manager tmux pane output."""
    subprocess.run(
        [
            "tmux", "pipe-pane", "-t",
            f"{TMUX_SESSION}:{TMUX_MANAGER_WINDOW}",
        ],
        check=True,
    )
    print(f"  Log capture stopped.")


def filter_logs():
    """Filter captured logs for rolling-update-related entries."""
    if not LOG_FILE.exists():
        print("  No log file found.")
        return
    filtered_lines = []
    for line in LOG_FILE.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if LOG_EXCLUDE_REGEX.search(stripped):
            continue
        if LOG_FILTER_REGEX.search(stripped):
            filtered_lines.append(stripped)

    FILTERED_LOG_FILE.write_text("\n".join(filtered_lines) + "\n")
    print(f"\n  Filtered {len(filtered_lines)} lines → {FILTERED_LOG_FILE}")
    return filtered_lines


def get_routes_snapshot(deployment_global_id):
    """Get a snapshot of all routes for the deployment."""
    result = gql_request(SEARCH_ROUTES_QUERY, {
        "deploymentId": deployment_global_id,
        "first": 50,
        "offset": 0,
    })
    if result.get("errors"):
        return []
    edges = result["data"]["routes"]["edges"]
    return [edge["node"] for edge in edges]


def format_routes_table(routes, deploying_revision_raw_id=None):
    """Format routes as a readable table with Old/New labels."""
    if not routes:
        return "  (no routes)"
    lines = []
    lines.append(f"  {'Rev':>5} | {'Status':<14} | {'Traffic':<12} | Route ID (short) | Session ID (short)")
    lines.append(f"  {'─'*5}─┼─{'─'*14}─┼─{'─'*12}─┼─{'─'*18}┼─{'─'*20}")
    for route in routes:
        revision_id_value = route.get("revisionId", "N/A")
        revision_raw_id = _safe_decode_id(revision_id_value)
        is_new = (deploying_revision_raw_id and revision_raw_id == deploying_revision_raw_id)
        rev_label = "NEW" if is_new else "OLD"
        route_short = _safe_decode_id(route.get("id", ""))[:8] or "N/A"
        session_short = route.get("sessionId", "N/A")
        if session_short and session_short != "N/A":
            session_short = session_short[:8]
        lines.append(
            f"  {rev_label:>5} | {route['status']:<14} | {route.get('trafficStatus', 'N/A'):<12} | {route_short:<18}| {session_short}"
        )
    return "\n".join(lines)


def get_db_deployment_state(deployment_raw_id):
    """Query DB directly for deployment state (sub_step, current/deploying revision)."""
    try:
        result = subprocess.run(
            [
                "docker", "exec", "main-backendai-half-db-1",
                "psql", "-U", "postgres", "-d", "backend", "-t", "-A", "-c",
                f"SELECT lifecycle_stage, sub_step, current_revision::text, deploying_revision::text "
                f"FROM endpoints WHERE id = '{deployment_raw_id}';",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip():
            parts = result.stdout.strip().split("|")
            return {
                "lifecycle_stage": parts[0] if len(parts) > 0 else "N/A",
                "sub_step": parts[1] if len(parts) > 1 else "N/A",
                "current_revision": parts[2][:8] if len(parts) > 2 and parts[2] else "None",
                "deploying_revision": parts[3][:8] if len(parts) > 3 and parts[3] else "None",
            }
    except Exception as error:
        return {"error": str(error)}
    return {}


# ── E2E Steps ──

def step_create_deployment():
    print("=" * 80)
    print(f"[Step 1] Creating deployment with {DESIRED_REPLICA_COUNT} replicas (Rolling strategy)...")
    variables = {
        "input": {
            "metadata": {
                "projectId": PROJECT_ID,
                "domainName": DOMAIN_NAME,
                "name": f"rolling-e2e-{int(time.time())}",
                "tags": ["e2e-test", "rolling-update"],
            },
            "networkAccess": {
                "openToPublic": False,
            },
            "defaultDeploymentStrategy": {
                "type": "ROLLING",
                "rollingUpdate": {
                    "maxSurge": 1,
                    "maxUnavailable": 0,
                },
            },
            "desiredReplicaCount": DESIRED_REPLICA_COUNT,
            "initialRevision": make_revision_input("v1", MODEL_VFOLDER_ID),
        },
    }
    result = gql_request(CREATE_DEPLOYMENT_MUTATION, variables)
    if result.get("errors"):
        sys.exit(1)
    deployment = result["data"]["createModelDeployment"]["deployment"]
    deployment_global_id = deployment["id"]
    deployment_raw_id = decode_global_id(deployment_global_id)
    print(f"  Deployment ID: {deployment_raw_id}")
    print(f"  Status: {deployment['metadata']['status']}")
    print(f"  Strategy: {deployment['defaultDeploymentStrategy']['type']}")
    print(f"  Replicas: {deployment['replicaState']['desiredReplicaCount']}")
    return deployment_global_id, deployment_raw_id


def step_poll_until_ready(deployment_global_id, deployment_raw_id, step_label):
    """Poll until deployment reaches READY/RUNNING with all routes HEALTHY."""
    print(f"\n{'=' * 80}")
    print(f"[{step_label}] Polling until deployment is ready with healthy routes...")
    start_time = time.time()
    last_snapshot = None
    while time.time() - start_time < POLL_TIMEOUT_SECONDS:
        result = gql_request(GET_DEPLOYMENT_QUERY, {"id": deployment_global_id})
        deployment = result["data"]["deployment"]
        status = deployment["metadata"]["status"]
        revision = deployment.get("revision")
        revision_name = revision["name"] if revision else "N/A"
        elapsed = int(time.time() - start_time)

        routes = get_routes_snapshot(deployment_global_id)
        db_state = get_db_deployment_state(deployment_raw_id)

        route_statuses = [r["status"] for r in routes]
        snapshot = f"status={status},routes={','.join(sorted(route_statuses))}"
        if snapshot != last_snapshot:
            print(f"\n  [{elapsed:>4}s] status={status}, revision={revision_name}")
            print(f"         DB: lifecycle={db_state.get('lifecycle_stage')}, sub_step={db_state.get('sub_step')}")
            print(f"         Routes ({len(routes)}):")
            print(format_routes_table(routes))
            last_snapshot = snapshot

        # Consider ready when status is READY/RUNNING and all routes are HEALTHY
        if status in ("READY", "RUNNING"):
            healthy_count = sum(1 for s in route_statuses if s == "HEALTHY")
            if healthy_count >= DESIRED_REPLICA_COUNT:
                print(f"\n  -> Deployment ready with {healthy_count} HEALTHY routes")
                return result
        if status in ("DESTROYED", "ERROR"):
            print(f"\n  X Unexpected terminal status: {status}")
            sys.exit(1)
        time.sleep(POLL_INTERVAL_SECONDS)
    print(f"  Timeout after {POLL_TIMEOUT_SECONDS}s")
    sys.exit(1)


def step_add_revision(deployment_raw_id):
    print(f"\n{'=' * 80}")
    print("[Step 3] Adding new revision v2...")
    variables = {
        "input": {
            "deploymentId": deployment_raw_id,
            **make_revision_input("v2", MODEL_VFOLDER_ID),
        },
    }
    result = gql_request(ADD_REVISION_MUTATION, variables)
    if result.get("errors"):
        sys.exit(1)
    revision = result["data"]["addModelRevision"]["revision"]
    revision_global_id = revision["id"]
    revision_raw_id = decode_global_id(revision_global_id)
    print(f"  New Revision ID: {revision_raw_id}")
    return revision_raw_id


def step_activate_revision(deployment_raw_id, revision_raw_id):
    print(f"\n{'=' * 80}")
    print(f"[Step 4] Activating revision v2 (triggers Rolling Update)...")
    variables = {
        "input": {
            "deploymentId": deployment_raw_id,
            "revisionId": revision_raw_id,
        },
    }
    result = gql_request(ACTIVATE_REVISION_MUTATION, variables)
    if result.get("errors"):
        sys.exit(1)
    data = result["data"]["activateDeploymentRevision"]
    print(f"  Previous Revision: {data.get('previousRevisionId', 'N/A')}")
    print(f"  Activated Revision: {data.get('activatedRevisionId', 'N/A')}")
    print(f"  Deployment Status: {data['deployment']['metadata']['status']}")
    return result


def step_poll_rolling_update(deployment_global_id, deployment_raw_id, deploying_revision_raw_id):
    """Poll rolling update progress, printing each cycle's state."""
    print(f"\n{'=' * 80}")
    print("[Step 5] Monitoring rolling update cycles...")
    print(f"  Target: {DESIRED_REPLICA_COUNT} replicas, maxSurge=1, maxUnavailable=0")
    print(f"  Deploying revision: {deploying_revision_raw_id[:8]}...")

    start_time = time.time()
    cycle_number = 0
    last_state_key = None

    while time.time() - start_time < POLL_TIMEOUT_SECONDS:
        result = gql_request(GET_DEPLOYMENT_QUERY, {"id": deployment_global_id})
        deployment = result["data"]["deployment"]
        status = deployment["metadata"]["status"]
        revision = deployment.get("revision")
        revision_name = revision["name"] if revision else "N/A"

        routes = get_routes_snapshot(deployment_global_id)
        db_state = get_db_deployment_state(deployment_raw_id)

        # Build state key from route statuses for change detection
        old_routes = []
        new_routes = []
        for route in routes:
            rev_raw = _safe_decode_id(route.get("revisionId", ""))
            if rev_raw == deploying_revision_raw_id:
                new_routes.append(route)
            else:
                old_routes.append(route)

        state_key = (
            f"{status}|{db_state.get('sub_step')}|"
            f"old={','.join(sorted(r['status'] for r in old_routes))}|"
            f"new={','.join(sorted(r['status'] for r in new_routes))}"
        )

        elapsed = int(time.time() - start_time)

        if state_key != last_state_key:
            old_status_summary = _summarize_routes(old_routes)
            new_status_summary = _summarize_routes(new_routes)

            print(f"\n  ┌─ Cycle {cycle_number} [{elapsed:>4}s] ──────────────────────────────────────")
            print(f"  │ GQL status    : {status}")
            print(f"  │ GQL revision  : {revision_name}")
            print(f"  │ DB lifecycle  : {db_state.get('lifecycle_stage')}")
            print(f"  │ DB sub_step   : {db_state.get('sub_step')}")
            print(f"  │ DB current_rev: {db_state.get('current_revision')}")
            print(f"  │ DB deploy_rev : {db_state.get('deploying_revision')}")
            print(f"  │")
            print(f"  │ Old (v1) routes: {len(old_routes)}  {old_status_summary}")
            print(f"  │ New (v2) routes: {len(new_routes)}  {new_status_summary}")
            print(f"  │")
            print(f"  │ All routes:")
            print(format_routes_table(routes, deploying_revision_raw_id))
            print(f"  └────────────────────────────────────────────────────────")

            last_state_key = state_key
            cycle_number += 1

        if status in ("READY", "RUNNING"):
            # Check if revision swapped to v2
            if revision and _safe_decode_id(revision["id"]) == deploying_revision_raw_id:
                healthy_new = sum(1 for r in new_routes if r["status"] == "HEALTHY")
                if healthy_new >= DESIRED_REPLICA_COUNT and len(old_routes) == 0:
                    print(f"\n  -> Rolling update COMPLETE! Current revision is now v2.")
                    return result
            elif db_state.get("deploying_revision") == "None" and db_state.get("sub_step") in ("None", ""):
                print(f"\n  -> Rolling update COMPLETE! Revision swap done.")
                return result

        if status in ("DESTROYED", "ERROR"):
            print(f"\n  ✗ Unexpected terminal status: {status}")
            sys.exit(1)

        time.sleep(POLL_INTERVAL_SECONDS)

    print(f"  Timeout after {POLL_TIMEOUT_SECONDS}s")
    sys.exit(1)


def _summarize_routes(routes):
    """Summarize route statuses as a compact string like [■ ■ ◇]."""
    if not routes:
        return "[]"
    symbols = []
    for route in routes:
        status = route["status"]
        if status == "HEALTHY":
            symbols.append("■")
        elif status in ("PROVISIONING", "PULLING"):
            symbols.append("◇")
        elif status == "UNHEALTHY":
            symbols.append("△")
        elif status in ("TERMINATING", "TERMINATED"):
            symbols.append("×")
        else:
            symbols.append("?")
    status_counts = {}
    for route in routes:
        status_counts[route["status"]] = status_counts.get(route["status"], 0) + 1
    count_str = ", ".join(f"{s}={c}" for s, c in sorted(status_counts.items()))
    return f"[{' '.join(symbols)}]  ({count_str})"


def step_final_check(deployment_global_id, deployment_raw_id):
    print(f"\n{'=' * 80}")
    print("[Step 6] Final state verification...")
    routes = get_routes_snapshot(deployment_global_id)
    db_state = get_db_deployment_state(deployment_raw_id)
    print(f"  DB: lifecycle={db_state.get('lifecycle_stage')}, sub_step={db_state.get('sub_step')}")
    print(f"  DB: current_revision={db_state.get('current_revision')}, deploying_revision={db_state.get('deploying_revision')}")
    print(f"  Routes ({len(routes)}):")
    print(format_routes_table(routes))


def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║        Rolling Update E2E Test — Replica Count 3, with Log Capture          ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()

    # Start log capture
    print("[Setup] Starting manager log capture...")
    start_log_capture()
    # Mark the start time so we can correlate logs
    test_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Test start time: {test_start_time}")

    try:
        # Step 1: Create deployment
        deployment_global_id, deployment_raw_id = step_create_deployment()

        # Step 2: Wait for all 3 replicas to be RUNNING
        step_poll_until_ready(deployment_global_id, deployment_raw_id, "Step 2")

        # Step 3: Add revision v2
        revision_raw_id = step_add_revision(deployment_raw_id)

        # Step 4: Activate revision v2 (triggers rolling update)
        step_activate_revision(deployment_raw_id, revision_raw_id)

        # Step 5: Monitor rolling update cycles
        step_poll_rolling_update(
            deployment_global_id,
            deployment_raw_id,
            revision_raw_id,
        )

        # Step 6: Final verification
        step_final_check(deployment_global_id, deployment_raw_id)

    finally:
        # Stop log capture
        print(f"\n{'=' * 80}")
        print("[Cleanup] Stopping log capture...")
        stop_log_capture()

    # Filter and display relevant logs
    print(f"\n{'=' * 80}")
    print("[Logs] Filtering manager logs for rolling-update-related entries...")
    filtered_lines = filter_logs()
    if filtered_lines:
        print(f"\n{'─' * 80}")
        print("  FILTERED MANAGER LOGS (rolling-update related)")
        print(f"{'─' * 80}")
        for line in filtered_lines:
            print(f"  {line}")
        print(f"{'─' * 80}")
    else:
        print("  No matching log lines found.")

    print(f"\n{'=' * 80}")
    print("E2E Test Complete!")
    print(f"  Raw logs     : {LOG_FILE}")
    print(f"  Filtered logs: {FILTERED_LOG_FILE}")


if __name__ == "__main__":
    main()
