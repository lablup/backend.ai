#!/usr/bin/env python3
"""
vLLM Deployment + Auto-Scaling E2E Test.

1. Deploy vLLM model service (1 replica)
2. Wait for HEALTHY
3. Create auto-scaling rule (INFERENCE_FRAMEWORK / vllm_num_requests_running)
4. Send inference requests → verify replica count increases
5. Cleanup

Usage:
  ./py scripts/test_vllm_autoscaling_e2e.py
  ./py scripts/test_vllm_autoscaling_e2e.py --cleanup <deployment_id>
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
import yarl
from dateutil.tz import tzutc

from ai.backend.client.auth import generate_signature

# ─────────────────────────────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────────────────────────────

API_ENDPOINT = yarl.URL("http://127.0.0.1:8091")
API_VERSION = "v8.20240915"
ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HASH_TYPE = "sha256"

DOMAIN_NAME = "default"
RESOURCE_GROUP = "default"

IMAGE_REF = "cr.backend.ai/multiarch/vllm:0.9.1-cuda12.8-ubuntu24.04-compat"
IMAGE_ARCH = "x86_64"

VFOLDER_ID = "0a065d0c-c25b-4463-9078-54f43463b32a"  # existing model VFolder UUID

RESOURCE_SLOTS = [
    {"resourceType": "cpu", "quantity": "4"},
    {"resourceType": "mem", "quantity": "17179869184"},
    {"resourceType": "cuda.device", "quantity": "1"},
]

# Auto-scaling: vLLM metrics via INFERENCE_FRAMEWORK
# vllm_num_requests_running > 1 → scale up
AUTOSCALE_METRIC_SOURCE = "INFERENCE_FRAMEWORK"
AUTOSCALE_METRIC_NAME = "requests_running"
AUTOSCALE_MAX_THRESHOLD = "1"
AUTOSCALE_STEP_SIZE = 1
AUTOSCALE_TIME_WINDOW = 30
AUTOSCALE_MIN_REPLICAS = 1
AUTOSCALE_MAX_REPLICAS = 5

# Inference load: model name inside container, concurrent requests
VLLM_MODEL_NAME = "/models/Qwen2.5-0.5B-Instruct"
LOAD_CONCURRENT_REQUESTS = 8
LOAD_MAX_TOKENS = 2048
LOAD_ROUNDS = 3
COOLDOWN_BETWEEN_ROUNDS = 90

POLL_INTERVAL = 5
POLL_TIMEOUT = 600

# ─────────────────────────────────────────────────────────────────────
#  GQL
# ─────────────────────────────────────────────────────────────────────

ADMIN_PROJECTS_V2 = """
query($filter: ProjectV2Filter, $limit: Int, $offset: Int) {
  adminProjectsV2(filter: $filter, limit: $limit, offset: $offset) {
    edges { node { id basicInfo { name } } }
  }
}"""

ADMIN_IMAGES_V2 = """
query($filter: ImageV2Filter, $limit: Int, $offset: Int) {
  adminImagesV2(filter: $filter, limit: $limit, offset: $offset) {
    edges { node { id identity { canonicalName architecture } } }
  }
}"""

CREATE_DEPLOYMENT = """
mutation($input: CreateDeploymentInput!) {
  createModelDeployment(input: $input) {
    deployment {
      id
      metadata { name status }
      networkAccess { endpointUrl }
      replicaState { desiredReplicaCount }
    }
  }
}"""

GET_DEPLOYMENT = """
query($id: ID!) {
  deployment(id: $id) {
    id
    metadata { name status }
    networkAccess { endpointUrl }
    replicaState { desiredReplicaCount }
  }
}"""

SEARCH_ROUTES = """
query($deploymentId: ID!, $limit: Int, $offset: Int) {
  routes(deploymentId: $deploymentId, limit: $limit, offset: $offset) {
    edges { node { id status sessionId } } count
  }
}"""

ADD_REVISION = """
mutation($input: AddRevisionInput!) {
  addModelRevision(input: $input) {
    revision { id name }
  }
}"""

ACTIVATE_REVISION = """
mutation($input: ActivateRevisionInput!) {
  activateDeploymentRevision(input: $input) {
    deployment { id metadata { status } }
    activatedRevisionId
  }
}"""

CREATE_AUTOSCALING_RULE = """
mutation($input: CreateAutoScalingRuleInput!) {
  createAutoScalingRule(input: $input) {
    rule { id metricSource metricName maxThreshold stepSize timeWindow minReplicas maxReplicas }
  }
}"""

DELETE_DEPLOYMENT = """
mutation($input: DeleteDeploymentInput!) {
  deleteModelDeployment(input: $input) { id }
}"""

# ─────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────

def gql(query: str, variables: dict | None = None) -> dict:
    date = datetime.now(tzutc())
    headers, _ = generate_signature(
        method="POST", version=API_VERSION, endpoint=API_ENDPOINT,
        date=date, rel_url="/admin/gql/strawberry",
        content_type="application/json",
        access_key=ACCESS_KEY, secret_key=SECRET_KEY, hash_type=HASH_TYPE,
    )
    headers = {**headers, "Content-Type": "application/json",
               "X-BackendAI-Version": API_VERSION, "Date": date.isoformat()}
    body: dict = {"query": query}
    if variables:
        body["variables"] = variables
    result = requests.post(str(API_ENDPOINT / "admin/gql/strawberry"), headers=headers, json=body).json()
    if result.get("errors"):
        print(f"  GQL errors: {json.dumps(result['errors'], indent=2)}")
    return result


def decode_gid(global_id: str) -> str:
    return base64.b64decode(global_id).decode().split(":")[1]


# ─────────────────────────────────────────────────────────────────────
#  Lookups
# ─────────────────────────────────────────────────────────────────────

def lookup_project_id() -> str:
    result = gql(ADMIN_PROJECTS_V2, {
        "filter": {"name": {"equals": "default"}, "domainName": {"equals": DOMAIN_NAME}},
        "limit": 1,
        "offset": 0,
    })
    data = result.get("data") or {}
    edges = data.get("adminProjectsV2", {}).get("edges", [])
    if not edges:
        sys.exit("ERROR: default project not found")
    project_global_id = edges[0]["node"]["id"]
    project_id = decode_gid(project_global_id)
    print(f"  Project : {project_id}")
    return project_id


def lookup_image_id() -> str:
    result = gql(ADMIN_IMAGES_V2, {
        "filter": {"name": {"equals": IMAGE_REF}, "architecture": {"equals": IMAGE_ARCH}},
        "limit": 1,
        "offset": 0,
    })
    data = result.get("data") or {}
    edges = data.get("adminImagesV2", {}).get("edges", [])
    if not edges:
        sys.exit(f"ERROR: image not found: {IMAGE_REF}")
    image_global_id = edges[0]["node"]["id"]
    image_id = decode_gid(image_global_id)
    print(f"  Image   : {image_id}")
    return image_id


# ─────────────────────────────────────────────────────────────────────
#  Deployment
# ─────────────────────────────────────────────────────────────────────

def create_deployment(name: str, project_id: str, image_id: str) -> tuple[str, str]:
    result = gql(CREATE_DEPLOYMENT, {"input": {
        "metadata": {"projectId": project_id, "domainName": DOMAIN_NAME, "name": name, "tags": ["e2e-test"]},
        "networkAccess": {"openToPublic": False},
        "defaultDeploymentStrategy": {"type": "ROLLING", "rollingUpdate": {"maxSurge": {"count": 1}, "maxUnavailable": {"count": 0}}},
        "desiredReplicaCount": 1,
        "initialRevision": {
            "name": "v1",
            "clusterConfig": {"mode": "SINGLE_NODE", "size": 1},
            "resourceConfig": {"resourceGroup": {"name": RESOURCE_GROUP}, "resourceSlots": {"entries": RESOURCE_SLOTS}},
            "image": {"id": image_id},
            "modelRuntimeConfig": {"runtimeVariant": "custom"},
            "modelMountConfig": {"vfolderId": VFOLDER_ID, "mountDestination": "/models", "definitionPath": "model-definition.yaml"},
            "extraMounts": [],
        },
    }})
    if result.get("errors"):
        sys.exit(1)
    deployment = result["data"]["createModelDeployment"]["deployment"]
    global_id = deployment["id"]
    raw_id = decode_gid(global_id)
    print(f"  Deployment: {raw_id}  status={deployment['metadata']['status']}")
    return global_id, raw_id


def add_and_activate_revision(deployment_raw_id: str, image_id: str) -> str:
    """Add initial revision and activate it so sokovan can schedule the deployment."""
    result = gql(ADD_REVISION, {"input": {
        "deploymentId": deployment_raw_id,
        "name": "v1",
        "clusterConfig": {"mode": "SINGLE_NODE", "size": 1},
        "resourceConfig": {"resourceGroup": {"name": RESOURCE_GROUP}, "resourceSlots": {"entries": RESOURCE_SLOTS}},
        "image": {"id": image_id},
        "modelRuntimeConfig": {"runtimeVariant": "custom"},
        "modelMountConfig": {"vfolderId": VFOLDER_ID, "mountDestination": "/models", "definitionPath": "model-definition.yaml"},
        "extraMounts": [],
    }})
    if result.get("errors"):
        sys.exit("ERROR: failed to add revision")
    revision_global_id = result["data"]["addModelRevision"]["revision"]["id"]
    revision_raw_id = decode_gid(revision_global_id)
    print(f"  Revision: {revision_raw_id}")

    act_result = gql(ACTIVATE_REVISION, {"input": {
        "deploymentId": deployment_raw_id,
        "revisionId": revision_raw_id,
    }})
    if act_result.get("errors"):
        sys.exit("ERROR: failed to activate revision")
    print(f"  Activated revision → status={act_result['data']['activateDeploymentRevision']['deployment']['metadata']['status']}")
    return revision_raw_id


def get_routes(deployment_global_id: str) -> list[dict]:
    result = gql(SEARCH_ROUTES, {"deploymentId": deployment_global_id, "limit": 50, "offset": 0})
    if result.get("errors") or not result.get("data"):
        return []
    return [edge["node"] for edge in result["data"]["routes"]["edges"]]


def wait_for_healthy(deployment_global_id: str, timeout: int = POLL_TIMEOUT) -> bool:
    print(f"  Waiting for HEALTHY (timeout {timeout}s)...")
    start = time.time()
    last_status = ""
    while time.time() - start < timeout:
        statuses = [r["status"] for r in get_routes(deployment_global_id)]
        status_key = ",".join(sorted(statuses)) or "(no routes)"
        if status_key != last_status:
            print(f"  [{int(time.time() - start):>4}s] {status_key}")
            last_status = status_key
        if any(s == "HEALTHY" for s in statuses):
            print(f"  HEALTHY at {time.time() - start:.0f}s")
            return True
        time.sleep(POLL_INTERVAL)
    return False


# ─────────────────────────────────────────────────────────────────────
#  Auto-scaling
# ─────────────────────────────────────────────────────────────────────

def create_autoscaling_rule(deployment_raw_id: str) -> str:
    result = gql(CREATE_AUTOSCALING_RULE, {"input": {
        "modelDeploymentId": deployment_raw_id,
        "metricSource": AUTOSCALE_METRIC_SOURCE,
        "metricName": AUTOSCALE_METRIC_NAME,
        "minThreshold": None,
        "maxThreshold": AUTOSCALE_MAX_THRESHOLD,
        "stepSize": AUTOSCALE_STEP_SIZE,
        "timeWindow": AUTOSCALE_TIME_WINDOW,
        "minReplicas": AUTOSCALE_MIN_REPLICAS,
        "maxReplicas": AUTOSCALE_MAX_REPLICAS,
    }})
    if result.get("errors"):
        sys.exit("ERROR: failed to create auto-scaling rule")
    rule = result["data"]["createAutoScalingRule"]["rule"]
    rule_id = decode_gid(rule["id"])
    print(f"  Rule    : {rule_id}")
    print(f"  Metric  : {rule['metricSource']}/{rule['metricName']} > {rule['maxThreshold']}")
    print(f"  Replicas: [{rule['minReplicas']}, {rule['maxReplicas']}]  step={rule['stepSize']}")
    return rule_id


# ─────────────────────────────────────────────────────────────────────
#  Inference load generation
# ─────────────────────────────────────────────────────────────────────

def get_inference_endpoint(deployment_global_id: str, deployment_raw_id: str) -> tuple[str, str]:
    """Return (endpoint_url, token) for sending inference requests."""
    result = gql(GET_DEPLOYMENT, {"id": deployment_global_id})
    endpoint_url = result["data"]["deployment"]["networkAccess"]["endpointUrl"]
    if not endpoint_url:
        sys.exit("ERROR: endpoint URL not found in deployment")

    cli_env = {
        "BACKEND_ENDPOINT": str(API_ENDPOINT), "BACKEND_ENDPOINT_TYPE": "api",
        "BACKEND_ACCESS_KEY": ACCESS_KEY, "BACKEND_SECRET_KEY": SECRET_KEY,
        "PATH": os.environ.get("PATH", ""),
    }
    result_cli = subprocess.run(
        ["./backend.ai", "service", "generate-token", deployment_raw_id, "1h"],
        capture_output=True, text=True, timeout=30, env=cli_env,
    )
    # Strip ANSI escape codes before matching JWT
    clean_output = re.sub(r"\x1b\[[0-9;]*m", "", result_cli.stdout + result_cli.stderr)
    match = re.search(r"(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)", clean_output)
    if not match:
        sys.exit(f"ERROR: failed to generate token: {clean_output}")
    return endpoint_url, match.group(1)


def send_inference_request(endpoint_url: str, token: str) -> None:
    """Send a single long-running inference request to vLLM."""
    try:
        requests.post(
            f"{endpoint_url}v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"BackendAI {token}"},
            json={
                "model": VLLM_MODEL_NAME,
                "messages": [{"role": "user", "content": "Write a very long detailed essay about the history of computing."}],
                "max_tokens": LOAD_MAX_TOKENS,
            },
            timeout=120,
        )
    except Exception:
        pass


def generate_inference_load(endpoint_url: str, token: str, concurrent: int = LOAD_CONCURRENT_REQUESTS) -> None:
    """Fire concurrent inference requests to saturate the model."""
    print(f"  Sending {concurrent} concurrent inference requests...")
    with ThreadPoolExecutor(max_workers=concurrent) as pool:
        futures = [pool.submit(send_inference_request, endpoint_url, token) for _ in range(concurrent)]
        for future in futures:
            future.result()
    print(f"  Load batch complete.")


def sustained_load_generator(endpoint_url: str, token: str, stop_event: threading.Event,
                              concurrent: int = LOAD_CONCURRENT_REQUESTS) -> None:
    """Continuously send inference requests until stop_event is set."""
    while not stop_event.is_set():
        with ThreadPoolExecutor(max_workers=concurrent) as pool:
            futures = [pool.submit(send_inference_request, endpoint_url, token) for _ in range(concurrent)]
            for future in futures:
                future.result()
        if not stop_event.is_set():
            time.sleep(1)


# ─────────────────────────────────────────────────────────────────────
#  Scaling verification
# ─────────────────────────────────────────────────────────────────────

def get_desired_replicas(deployment_global_id: str) -> int:
    return gql(GET_DEPLOYMENT, {"id": deployment_global_id})["data"]["deployment"]["replicaState"]["desiredReplicaCount"]


def wait_for_scaling(deployment_global_id: str, minimum_replicas: int, timeout: int = 180) -> bool:
    print(f"  Waiting for replicas >= {minimum_replicas}...")
    start = time.time()
    last_printed = 0
    while time.time() - start < timeout:
        desired = get_desired_replicas(deployment_global_id)
        elapsed = int(time.time() - start)
        if elapsed - last_printed >= 10 or desired >= minimum_replicas:
            print(f"  [{elapsed:>4}s] desired_replicas={desired}")
            last_printed = elapsed
        if desired >= minimum_replicas:
            return True
        time.sleep(POLL_INTERVAL)
    return False


# ─────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not VFOLDER_ID:
        sys.exit("ERROR: set VFOLDER_ID")

    print("=" * 60)
    print("  vLLM Deployment + Auto-Scaling E2E")
    print("=" * 60)

    print("\n[1] Prerequisites")
    project_id = lookup_project_id()
    image_id = lookup_image_id()
    print(f"  VFolder : {VFOLDER_ID}")

    print("\n[2] Deploy")
    deployment_global_id, deployment_raw_id = create_deployment(f"vllm-e2e-{int(time.time())}", project_id, image_id)

    print("\n[2b] Add & Activate Initial Revision")
    add_and_activate_revision(deployment_raw_id, image_id)

    if not wait_for_healthy(deployment_global_id):
        sys.exit("Deployment never became HEALTHY")

    print("\n[3] Auto-Scaling Rule")
    create_autoscaling_rule(deployment_raw_id)

    print("\n[4] Get inference endpoint")
    endpoint_url, token = get_inference_endpoint(deployment_global_id, deployment_raw_id)
    print(f"  URL     : {endpoint_url}")

    print("\n[5] Sustained Load + Scaling Verification")
    print(f"  Starting sustained load ({LOAD_CONCURRENT_REQUESTS} concurrent requests)...")
    stop_event = threading.Event()
    load_thread = threading.Thread(
        target=sustained_load_generator,
        args=(endpoint_url, token, stop_event, LOAD_CONCURRENT_REQUESTS),
        daemon=True,
    )
    load_thread.start()

    target = 2
    if wait_for_scaling(deployment_global_id, target, timeout=300):
        print(f"  [PASS] Scaled to >= {target}")
    else:
        print(f"  [FAIL] Did not scale to >= {target}")

    stop_event.set()
    load_thread.join(timeout=30)

    final = get_desired_replicas(deployment_global_id)
    print(f"\n{'=' * 60}")
    print(f"  Deployment    : {deployment_raw_id}")
    print(f"  Final replicas: {final}")
    print(f"  Cleanup: ./py scripts/test_vllm_autoscaling_e2e.py --cleanup {deployment_raw_id}")


def cleanup(args: list[str]) -> None:
    if not args:
        sys.exit("Usage: --cleanup <deployment_id>")
    for deployment_id in args:
        print(f"  Destroying {deployment_id[:8]}...")
        gql(DELETE_DEPLOYMENT, {"input": {"id": deployment_id}})
    print("  Done.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup(sys.argv[2:])
    else:
        main()
