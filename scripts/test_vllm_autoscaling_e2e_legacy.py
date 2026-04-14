#!/usr/bin/env python3
"""
vLLM Deployment + Auto-Scaling E2E Test (26.3 legacy API).

1. Deploy vLLM via ./backend.ai service create
2. Wait for HEALTHY
3. Create auto-scaling rule via legacy GQL (create_endpoint_auto_scaling_rule)
4. Send inference requests → verify replica count increases
5. Cleanup

Usage:
  ./py scripts/test_vllm_autoscaling_e2e_legacy.py
  ./py scripts/test_vllm_autoscaling_e2e_legacy.py --cleanup <endpoint_id>
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
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

IMAGE_REF = "cr.backend.ai/multiarch/vllm:0.9.1-cuda12.8-ubuntu24.04"
VFOLDER_NAME = "vllm-test-model"  # existing model VFolder name
VLLM_MODEL_NAME = "/models/Qwen2.5-0.5B-Instruct"

RESOURCE_SLOTS = {"cpu": "4", "mem": "16g", "cuda.device": "1"}
SCALING_GROUP = "default"

# Auto-scaling
AUTOSCALE_METRIC_SOURCE = "INFERENCE_FRAMEWORK"
AUTOSCALE_METRIC_NAME = "vllm_num_requests_running"
AUTOSCALE_THRESHOLD = "1"
AUTOSCALE_COMPARATOR = "GREATER_THAN"
AUTOSCALE_STEP_SIZE = 1
AUTOSCALE_COOLDOWN = 60
AUTOSCALE_MIN_REPLICAS = 1
AUTOSCALE_MAX_REPLICAS = 5

# Load
LOAD_CONCURRENT_REQUESTS = 8
LOAD_MAX_TOKENS = 512
LOAD_ROUNDS = 3
COOLDOWN_BETWEEN_ROUNDS = 90

POLL_INTERVAL = 5
POLL_TIMEOUT = 600

BAI_CLI = "./backend.ai"
DB_CONTAINER = "main-backendai-half-db-1"

CLI_ENV = {
    **os.environ,
    "BACKEND_ENDPOINT": str(API_ENDPOINT),
    "BACKEND_ENDPOINT_TYPE": "api",
    "BACKEND_ACCESS_KEY": ACCESS_KEY,
    "BACKEND_SECRET_KEY": SECRET_KEY,
}

# ─────────────────────────────────────────────────────────────────────
#  Legacy GQL
# ─────────────────────────────────────────────────────────────────────

CREATE_AUTOSCALING_RULE_LEGACY = """
mutation($endpoint: String!, $props: EndpointAutoScalingRuleInput!) {
  create_endpoint_auto_scaling_rule_node(endpoint: $endpoint, props: $props) {
    ok msg
    rule { id metric_source metric_name threshold comparator step_size cooldown_seconds min_replicas max_replicas }
  }
}
"""

# ─────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────

def legacy_gql(query: str, variables: dict | None = None) -> dict:
    date = datetime.now(tzutc())
    headers, _ = generate_signature(
        method="POST", version=API_VERSION, endpoint=API_ENDPOINT,
        date=date, rel_url="/admin/graphql",
        content_type="application/json",
        access_key=ACCESS_KEY, secret_key=SECRET_KEY, hash_type=HASH_TYPE,
    )
    headers = {**headers, "Content-Type": "application/json",
               "X-BackendAI-Version": API_VERSION, "Date": date.isoformat()}
    body: dict = {"query": query}
    if variables:
        body["variables"] = variables
    result = requests.post(str(API_ENDPOINT / "admin/graphql"), headers=headers, json=body).json()
    if "errors" in result:
        print(f"  GQL errors: {json.dumps(result['errors'], indent=2)}")
    return result


def bai_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([BAI_CLI, *args], capture_output=True, text=True, timeout=60, env=CLI_ENV)


def db_query(sql: str) -> str:
    return subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", "postgres", "-d", "backend", "-t", "-A", "-c", sql],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip()


# ─────────────────────────────────────────────────────────────────────
#  Deploy via CLI
# ─────────────────────────────────────────────────────────────────────

def create_service() -> str:
    name = f"vllm-e2e-{int(time.time())}"
    resource_args = []
    for key, value in RESOURCE_SLOTS.items():
        resource_args += ["-r", f"{key}={value}"]

    result = bai_cli(
        "service", "create",
        IMAGE_REF, VFOLDER_NAME, "1",
        "-t", name,
        *resource_args,
        "--scaling-group", SCALING_GROUP,
    )
    if result.returncode != 0:
        sys.exit(f"ERROR creating service:\n{result.stdout}\n{result.stderr}")

    # Parse endpoint ID from output
    for line in result.stdout.splitlines():
        if "Endpoint Id" in line:
            endpoint_id = line.split()[-1]
            print(f"  Endpoint  : {endpoint_id}")
            print(f"  Name      : {name}")
            return endpoint_id
    sys.exit(f"ERROR: could not parse endpoint ID from:\n{result.stdout}")


def wait_for_healthy(endpoint_id: str, timeout: int = POLL_TIMEOUT) -> bool:
    print(f"  Waiting for HEALTHY (timeout {timeout}s)...")
    start = time.time()
    last_status = ""
    while time.time() - start < timeout:
        route_status = db_query(
            f"SELECT r.status FROM routings r "
            f"WHERE r.endpoint='{endpoint_id}' AND r.status != 'terminated';"
        )
        if route_status != last_status:
            print(f"  [{int(time.time() - start):>4}s] {route_status or '(no routes)'}")
            last_status = route_status
        if "healthy" in route_status:
            print(f"  HEALTHY at {time.time() - start:.0f}s")
            return True
        time.sleep(POLL_INTERVAL)
    return False


# ─────────────────────────────────────────────────────────────────────
#  Auto-scaling rule via legacy GQL
# ─────────────────────────────────────────────────────────────────────

def create_autoscaling_rule(endpoint_id: str) -> str:
    result = legacy_gql(CREATE_AUTOSCALING_RULE_LEGACY, {
        "endpoint": endpoint_id,
        "props": {
            "metric_source": AUTOSCALE_METRIC_SOURCE,
            "metric_name": AUTOSCALE_METRIC_NAME,
            "threshold": AUTOSCALE_THRESHOLD,
            "comparator": AUTOSCALE_COMPARATOR,
            "step_size": AUTOSCALE_STEP_SIZE,
            "cooldown_seconds": AUTOSCALE_COOLDOWN,
            "min_replicas": AUTOSCALE_MIN_REPLICAS,
            "max_replicas": AUTOSCALE_MAX_REPLICAS,
        },
    })
    data = result.get("data", {}).get("create_endpoint_auto_scaling_rule_node", {})
    if not data.get("ok"):
        sys.exit(f"ERROR creating rule: {data.get('msg')}")
    rule = data["rule"]
    print(f"  Rule      : {rule['id']}")
    print(f"  Metric    : {rule['metric_source']}/{rule['metric_name']} > {rule['threshold']}")
    print(f"  Replicas  : [{rule['min_replicas']}, {rule['max_replicas']}]  step={rule['step_size']}")
    print(f"  Cooldown  : {rule['cooldown_seconds']}s")
    return rule["id"]


# ─────────────────────────────────────────────────────────────────────
#  Inference load
# ─────────────────────────────────────────────────────────────────────

def get_inference_endpoint(endpoint_id: str) -> tuple[str, str]:
    endpoint_url = db_query(f"SELECT url FROM endpoints WHERE id='{endpoint_id}';")
    if not endpoint_url:
        sys.exit("ERROR: endpoint URL not found")
    result = bai_cli("service", "generate-token", endpoint_id, "1h")
    match = re.search(r"(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)", result.stdout)
    if not match:
        sys.exit(f"ERROR generating token:\n{result.stdout}\n{result.stderr}")
    return endpoint_url, match.group(1)


def send_inference_request(endpoint_url: str, token: str) -> None:
    try:
        requests.post(
            f"{endpoint_url}v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"BackendAI {token}"},
            json={
                "model": VLLM_MODEL_NAME,
                "messages": [{"role": "user", "content": "Write a detailed essay about computing history."}],
                "max_tokens": LOAD_MAX_TOKENS,
            },
            timeout=120,
        )
    except Exception:
        pass


def generate_inference_load(endpoint_url: str, token: str) -> None:
    print(f"  Sending {LOAD_CONCURRENT_REQUESTS} concurrent requests...")
    with ThreadPoolExecutor(max_workers=LOAD_CONCURRENT_REQUESTS) as pool:
        futures = [pool.submit(send_inference_request, endpoint_url, token) for _ in range(LOAD_CONCURRENT_REQUESTS)]
        for future in futures:
            future.result()
    print(f"  Load batch complete.")


# ─────────────────────────────────────────────────────────────────────
#  Scaling verification
# ─────────────────────────────────────────────────────────────────────

def get_desired_replicas(endpoint_id: str) -> int:
    row = db_query(f"SELECT desired_session_count FROM endpoints WHERE id='{endpoint_id}';")
    return int(row) if row else 1


def wait_for_scaling(endpoint_id: str, minimum_replicas: int, timeout: int = 180) -> bool:
    print(f"  Waiting for replicas >= {minimum_replicas}...")
    start = time.time()
    last_printed = 0
    while time.time() - start < timeout:
        desired = get_desired_replicas(endpoint_id)
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
    print("=" * 60)
    print("  vLLM Deployment + Auto-Scaling E2E (26.3 legacy)")
    print("=" * 60)

    print("\n[1] Deploy")
    endpoint_id = create_service()
    if not wait_for_healthy(endpoint_id):
        sys.exit("Deployment never became HEALTHY")

    print("\n[2] Auto-Scaling Rule")
    create_autoscaling_rule(endpoint_id)

    print("\n[3] Get inference endpoint")
    endpoint_url, token = get_inference_endpoint(endpoint_id)
    print(f"  URL     : {endpoint_url}")

    for round_number in range(1, LOAD_ROUNDS + 1):
        target = min(1 + round_number, AUTOSCALE_MAX_REPLICAS)
        print(f"\n[4.{round_number}] Load Round {round_number}/{LOAD_ROUNDS}  (target >= {target})")
        generate_inference_load(endpoint_url, token)
        if wait_for_scaling(endpoint_id, target):
            print(f"  [PASS] Scaled to >= {target}")
        else:
            print(f"  [FAIL] Did not scale to >= {target}")
        if round_number < LOAD_ROUNDS:
            print(f"  Cooldown {COOLDOWN_BETWEEN_ROUNDS}s...")
            time.sleep(COOLDOWN_BETWEEN_ROUNDS)

    final = get_desired_replicas(endpoint_id)
    print(f"\n{'=' * 60}")
    print(f"  Endpoint      : {endpoint_id}")
    print(f"  Final replicas: {final}")
    print(f"  Cleanup: ./py scripts/test_vllm_autoscaling_e2e_legacy.py --cleanup {endpoint_id}")


def cleanup(args: list[str]) -> None:
    if not args:
        sys.exit("Usage: --cleanup <endpoint_id>")
    for endpoint_id in args:
        print(f"  Removing {endpoint_id[:8]}...")
        bai_cli("service", "rm", endpoint_id)
    print("  Done.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup(sys.argv[2:])
    else:
        main()
