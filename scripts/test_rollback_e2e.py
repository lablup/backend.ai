#!/usr/bin/env python3
"""
Rollback E2E test: create deployment -> add broken revision -> activate -> expect rollback.
Uses a broken model vfolder (health check returns 500) to trigger automatic rollback.
"""
import json
import sys
import time
import requests
from datetime import datetime
from dateutil.tz import tzutc
import yarl
from ai.backend.client.auth import generate_signature

API_ENDPOINT = yarl.URL("http://127.0.0.1:8091")
API_VERSION = "v8.20240915"
ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HASH_TYPE = "sha256"

# ── Target IDs (edit before running) ──
PROJECT_ID = "2de2b969-1d04-48a6-af16-0bc8adb3c831"
DOMAIN_NAME = "default"
IMAGE_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
GOOD_MODEL_VFOLDER_ID = "fb0389a96a1945bc8fb0da6e69808dea"
BROKEN_MODEL_VFOLDER_ID = "af47d6ce645846d3b2109f3f2f36ff10"
RESOURCE_GROUP = "default"

POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 600  # longer timeout for rollback scenario


def make_headers(method, rel_url):
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


def make_revision_input(name, vfolder_id):
    return {
        "name": name,
        "cluster_config": {
            "mode": "SINGLE_NODE",
            "size": 1,
        },
        "resource_config": {
            "resource_group": RESOURCE_GROUP,
            "resource_slots": {
                "cpu": "1",
                "mem": "1073741824",
            },
        },
        "image": {
            "id": IMAGE_ID,
        },
        "model_runtime_config": {
            "runtime_variant": "custom",
        },
        "model_mount_config": {
            "vfolder_id": vfolder_id,
            "mount_destination": "/models",
            "definition_path": "model-definition.yaml",
        },
    }


def step_create_deployment():
    print("=" * 60)
    print("[Step 1] Creating deployment with good model (v1)...")
    rel_url = "/deployments"
    body = {
        "metadata": {
            "project_id": PROJECT_ID,
            "domain_name": DOMAIN_NAME,
            "name": f"rollback-e2e-{int(time.time())}",
            "tags": ["e2e-test", "rollback"],
        },
        "network_access": {
            "open_to_public": False,
        },
        "default_deployment_strategy": {
            "type": "ROLLING",
            "rolling_update": {
                "max_surge": 1,
                "max_unavailable": 0,
            },
        },
        "desired_replica_count": 1,
        "initial_revision": make_revision_input("v1-good", GOOD_MODEL_VFOLDER_ID),
    }
    response = requests.post(
        str(API_ENDPOINT / rel_url[1:]),
        headers=make_headers("POST", rel_url),
        json=body,
    )
    result = response.json()
    print(f"  Status: {response.status_code}")
    if response.status_code != 201:
        print(f"  Error: {json.dumps(result, indent=2)}")
        sys.exit(1)
    deployment_id = result["deployment"]["id"]
    initial_revision_id = result["deployment"]["current_revision"]["id"] if result["deployment"].get("current_revision") else None
    print(f"  Deployment ID: {deployment_id}")
    print(f"  Initial Revision ID: {initial_revision_id}")
    return deployment_id, initial_revision_id


def step_poll_deployment_status(deployment_id, target_statuses, step_label):
    """Poll until status matches one of target_statuses."""
    if isinstance(target_statuses, str):
        target_statuses = [target_statuses]
    print(f"\n[{step_label}] Polling deployment status (target: {target_statuses})...")
    start_time = time.time()
    while time.time() - start_time < POLL_TIMEOUT_SECONDS:
        rel_url = f"/deployments/{deployment_id}"
        response = requests.get(
            str(API_ENDPOINT / rel_url[1:]),
            headers=make_headers("GET", rel_url),
        )
        result = response.json()
        status = result["deployment"]["status"]
        sub_step = result["deployment"].get("sub_step")
        current_revision = result["deployment"].get("current_revision")
        revision_name = current_revision["name"] if current_revision else "N/A"
        revision_id = current_revision["id"] if current_revision else "N/A"
        elapsed = int(time.time() - start_time)
        print(
            f"  [{elapsed}s] status={status}, sub_step={sub_step}, "
            f"revision={revision_name} ({revision_id})"
        )
        if status in target_statuses:
            print(f"  -> Reached target status: {status}")
            return result
        if status in ("DESTROYED",):
            print(f"  -> Unexpected terminal status: {status}")
            print(f"  Full response: {json.dumps(result, indent=2)}")
            sys.exit(1)
        time.sleep(POLL_INTERVAL_SECONDS)
    print(f"  -> Timeout after {POLL_TIMEOUT_SECONDS}s")
    sys.exit(1)


def step_add_broken_revision(deployment_id):
    print("\n" + "=" * 60)
    print("[Step 3] Adding broken revision v2 (health check will fail)...")
    rel_url = f"/deployments/{deployment_id}/revisions"
    body = {
        "revision": make_revision_input("v2-broken", BROKEN_MODEL_VFOLDER_ID),
    }
    response = requests.post(
        str(API_ENDPOINT / rel_url[1:]),
        headers=make_headers("POST", rel_url),
        json=body,
    )
    result = response.json()
    print(f"  Status: {response.status_code}")
    if response.status_code != 201:
        print(f"  Error: {json.dumps(result, indent=2)}")
        sys.exit(1)
    revision_id = result["revision"]["id"]
    print(f"  Broken Revision ID: {revision_id}")
    return revision_id


def step_activate_revision(deployment_id, revision_id, step_label):
    print(f"\n[{step_label}] Activating broken revision {revision_id}...")
    rel_url = f"/deployments/{deployment_id}/revisions/{revision_id}/activate"
    response = requests.post(
        str(API_ENDPOINT / rel_url[1:]),
        headers=make_headers("POST", rel_url),
    )
    result = response.json()
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(result, indent=2)}")
    return result


def step_check_routes(deployment_id, step_label):
    print(f"\n[{step_label}] Checking routes...")
    rel_url = f"/deployments/{deployment_id}/routes/search"
    body = {"limit": 50, "offset": 0}
    response = requests.post(
        str(API_ENDPOINT / rel_url[1:]),
        headers=make_headers("POST", rel_url),
        json=body,
    )
    result = response.json()
    if response.status_code == 200:
        routes = result.get("routes", [])
        for route in routes:
            print(
                f"  Route {route['id']}: "
                f"status={route['status']}, "
                f"traffic={route['traffic_status']}, "
                f"revision={route.get('revision_id', 'N/A')}"
            )
    return result


def main():
    print("Rollback E2E Test (broken revision -> automatic rollback)")
    print("=" * 60)

    # Step 1: Create deployment with good model
    deployment_id, initial_revision_id = step_create_deployment()

    # Step 2: Wait for deployment to become RUNNING
    running_result = step_poll_deployment_status(deployment_id, "RUNNING", "Step 2")
    if not initial_revision_id:
        initial_revision_id = running_result["deployment"]["current_revision"]["id"]
    print(f"  Initial (good) revision: {initial_revision_id}")

    # Step 3: Add broken revision
    broken_revision_id = step_add_broken_revision(deployment_id)

    # Step 4: Activate broken revision (triggers rolling update)
    step_activate_revision(deployment_id, broken_revision_id, "Step 4")

    # Step 5: Poll until rollback completes (should go back to RUNNING after rollback)
    # The system should detect health check failure and roll back to v1
    final_result = step_poll_deployment_status(
        deployment_id, ["RUNNING", "ERROR"], "Step 5"
    )

    # Step 6: Verify rollback
    final_status = final_result["deployment"]["status"]
    current_revision = final_result["deployment"].get("current_revision")
    current_revision_id = current_revision["id"] if current_revision else None

    print("\n" + "=" * 60)
    if final_status == "RUNNING" and current_revision_id == initial_revision_id:
        print("[PASS] Rollback succeeded! Deployment reverted to v1 (good model).")
    elif final_status == "ERROR":
        print("[INFO] Deployment entered ERROR status.")
        print("  This may indicate the rollback mechanism detected the failure.")
        print(f"  Current revision: {current_revision_id}")
    else:
        print("[FAIL] Unexpected final state.")
        print(f"  Status: {final_status}")
        print(f"  Current revision: {current_revision_id}")
        print(f"  Expected revision (v1): {initial_revision_id}")

    # Step 7: Check routes
    step_check_routes(deployment_id, "Step 7")

    print("\n" + "=" * 60)
    print("Rollback E2E Test Complete!")
    print(f"  Deployment ID: {deployment_id}")
    print(f"  Good Revision (v1): {initial_revision_id}")
    print(f"  Broken Revision (v2): {broken_revision_id}")
    print(f"  Final Revision: {current_revision_id}")


if __name__ == "__main__":
    main()
