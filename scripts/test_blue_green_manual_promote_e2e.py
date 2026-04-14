#!/usr/bin/env python3
"""
Blue-Green E2E test (auto_promote=false): create deployment -> add revision v2 -> activate v2.
With auto_promote=false, the strategy should reach AWAITING_PROMOTION and stay there
until manual promotion is triggered via the promote API.
"""
import json
import sys
import time

import requests
import yarl
from datetime import datetime
from dateutil.tz import tzutc
from ai.backend.client.auth import generate_signature

API_ENDPOINT = yarl.URL("http://127.0.0.1:8091")
API_VERSION = "v8.20240915"
ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HASH_TYPE = "sha256"

# ── Target IDs (edit before running) ──
PROJECT_ID = "2de2b969-1d04-48a6-af16-0bc8adb3c831"
DOMAIN_NAME = "default"
IMAGE_ID = "66ee9716-0fca-4092-8733-7cff18bd4eef"
MODEL_VFOLDER_ID = "fb0389a96a1945bc8fb0da6e69808dea"
RESOURCE_GROUP = "default"

POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 600


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
    print("[Step 1] Creating blue-green deployment (auto_promote=false)...")
    rel_url = "/deployments"
    body = {
        "metadata": {
            "project_id": PROJECT_ID,
            "domain_name": DOMAIN_NAME,
            "name": f"bg-manual-e2e-{int(time.time())}",
            "tags": ["e2e-test", "blue-green", "manual-promote"],
        },
        "network_access": {
            "open_to_public": False,
        },
        "default_deployment_strategy": {
            "type": "BLUE_GREEN",
            "blue_green": {
                "auto_promote": False,
                "promote_delay_seconds": 0,
            },
        },
        "desired_replica_count": 1,
        "initial_revision": make_revision_input("v1", MODEL_VFOLDER_ID),
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
    print(f"  Deployment ID: {deployment_id}")
    return deployment_id


def step_poll_deployment_status(deployment_id, target_status, step_label, target_sub_step=None):
    print(f"\n[{step_label}] Polling deployment status (target: {target_status}, sub_step: {target_sub_step})...")
    start_time = time.time()
    while time.time() - start_time < POLL_TIMEOUT_SECONDS:
        rel_url = f"/deployments/{deployment_id}"
        response = requests.get(
            str(API_ENDPOINT / rel_url[1:]),
            headers=make_headers("GET", rel_url),
        )
        result = response.json()
        deployment_data = result.get("deployment")
        if deployment_data is None:
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] Unexpected response: {json.dumps(result, indent=2)}")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        status = deployment_data["status"]
        sub_step = deployment_data.get("sub_step")
        current_revision = deployment_data.get("current_revision")
        revision_name = current_revision["name"] if current_revision else "N/A"
        elapsed = int(time.time() - start_time)
        print(f"  [{elapsed}s] status={status}, sub_step={sub_step}, revision={revision_name}")
        if status == target_status:
            if target_sub_step is None or sub_step == target_sub_step:
                print(f"  -> Reached target: status={target_status}, sub_step={target_sub_step}")
                return result
        if status in ("DESTROYED", "ERROR"):
            print(f"  -> Unexpected terminal status: {status}")
            print(f"  Full response: {json.dumps(result, indent=2)}")
            sys.exit(1)
        time.sleep(POLL_INTERVAL_SECONDS)
    print(f"  -> Timeout after {POLL_TIMEOUT_SECONDS}s")
    sys.exit(1)


def step_add_revision(deployment_id):
    print("\n" + "=" * 60)
    print("[Step 3] Adding new revision v2...")
    rel_url = f"/deployments/{deployment_id}/revisions"
    body = {
        "revision": make_revision_input("v2", MODEL_VFOLDER_ID),
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
    print(f"  New Revision ID: {revision_id}")
    return revision_id


def step_activate_revision(deployment_id, revision_id):
    print("\n" + "=" * 60)
    print(f"[Step 4] Activating revision {revision_id}...")
    rel_url = f"/deployments/{deployment_id}/revisions/{revision_id}/activate"
    response = requests.post(
        str(API_ENDPOINT / rel_url[1:]),
        headers=make_headers("POST", rel_url),
    )
    result = response.json()
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(result, indent=2)}")
    if response.status_code != 200:
        sys.exit(1)
    return result


def step_update_policy_to_auto_promote(deployment_id):
    print("\n" + "=" * 60)
    print("[Step 6] Updating policy to auto_promote=true to trigger promotion...")
    rel_url = f"/deployments/{deployment_id}/policy"
    body = {
        "strategy": "BLUE_GREEN",
        "blue_green": {
            "auto_promote": True,
            "promote_delay_seconds": 0,
        },
    }
    response = requests.put(
        str(API_ENDPOINT / rel_url[1:]),
        headers=make_headers("PUT", rel_url),
        json=body,
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
    else:
        print(f"  Error: {json.dumps(result, indent=2)}")
    return result


def main():
    print("Blue-Green E2E Test (auto_promote=false, AWAITING_PROMOTION expected)")
    print("=" * 60)

    # Step 1: Create deployment with blue-green strategy (auto_promote=false)
    deployment_id = step_create_deployment()

    # Step 2: Wait for deployment to become READY
    step_poll_deployment_status(deployment_id, "READY", "Step 2")

    # Step 3: Add revision v2
    revision_id = step_add_revision(deployment_id)

    # Step 4: Activate revision v2 (triggers blue-green deployment)
    step_activate_revision(deployment_id, revision_id)

    # Step 5: Poll until AWAITING_PROMOTION sub_step is reached
    print("\n" + "=" * 60)
    print("Expecting deployment to reach DEPLOYING / AWAITING_PROMOTION...")
    step_poll_deployment_status(
        deployment_id,
        "DEPLOYING",
        "Step 5",
        target_sub_step="deploying_awaiting_promotion",
    )
    print("  [PASS] Deployment reached AWAITING_PROMOTION as expected!")

    # Step 5b: Check routes while in AWAITING_PROMOTION
    step_check_routes(deployment_id, "Step 5b")

    # Step 6: Update policy to auto_promote=true to trigger promotion
    step_update_policy_to_auto_promote(deployment_id)

    # Step 7: Poll until deployment completes (back to READY)
    final_result = step_poll_deployment_status(deployment_id, "READY", "Step 7")

    # Step 8: Verify results
    current_revision = final_result["deployment"].get("current_revision")
    print("\n" + "=" * 60)
    if current_revision and current_revision["id"] == revision_id:
        print("[PASS] Blue-green deployment completed after manual promotion.")
        print(f"  Current revision is v2: {revision_id}")
    else:
        print("[FAIL] Current revision does not match the activated revision.")
        print(f"  Expected: {revision_id}")
        print(f"  Got: {current_revision['id'] if current_revision else 'None'}")
        sys.exit(1)

    # Step 9: Check routes
    step_check_routes(deployment_id, "Step 9")

    print("\n" + "=" * 60)
    print("E2E Test Complete!")
    print(f"  Deployment ID: {deployment_id}")
    print(f"  Final Revision ID: {revision_id}")


if __name__ == "__main__":
    main()
