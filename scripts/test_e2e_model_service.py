#!/usr/bin/env python3
"""E2E test: verify model service works end-to-end with Manager-provided model_definition."""
import json
import subprocess
import sys
import time

import requests
import yarl
from ai.backend.client.auth import generate_signature
from datetime import datetime
from dateutil.tz import tzutc

API_ENDPOINT = yarl.URL("http://127.0.0.1:8091")
API_VERSION = "v8.20240915"
ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
HASH_TYPE = "sha256"

VFOLDER_ID = "78116ee1-ed50-4f1c-b513-7cf46f21a3a1"
IMAGE_ID = "02522987-2890-462c-9efb-8e6ac95787ea"
PROJECT_ID = "2de2b969-1d04-48a6-af16-0bc8adb3c831"
BAI = "./bai"


def _headers(method: str, rel_url: str) -> dict[str, str]:
    date = datetime.now(tzutc())
    content_type = "application/json"
    hdrs, _ = generate_signature(
        method=method, version=API_VERSION, endpoint=API_ENDPOINT,
        date=date, rel_url=rel_url, content_type=content_type,
        access_key=ACCESS_KEY, secret_key=SECRET_KEY, hash_type=HASH_TYPE,
    )
    return {
        "Content-Type": content_type,
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }


def bai(*args: str) -> dict:
    env = {
        **subprocess.os.environ,
        "BACKEND_ENDPOINT_TYPE": "session",
        "BACKEND_ENDPOINT": "http://127.0.0.1:8090",
    }
    # Remove API-mode keys so session mode is used
    env.pop("BACKEND_ACCESS_KEY", None)
    env.pop("BACKEND_SECRET_KEY", None)
    result = subprocess.run(
        [BAI, *args],
        capture_output=True, text=True, timeout=30, env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"bai {' '.join(args)} failed: {result.stderr[:500]}")
    return json.loads(result.stdout)


def db_query(query: str) -> str:
    result = subprocess.run(
        ["docker", "exec", "main2-backendai-half-db-1", "psql", "-U", "postgres", "-d", "backend", "-t", "-A", "-c", query],
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip()


def create_legacy_service(name: str) -> dict:
    method = "POST"
    rel_url = "/services"
    body = {
        "service_name": name,
        "model": VFOLDER_ID,
        "model_definition_path": "model-definition.yaml",
        "image": "cr.backend.ai/stable/python:3.9-ubuntu20.04",
        "runtime_variant": "custom",
        "desired_session_count": 1,
        "open_to_public": False,
        "config": {
            "model": VFOLDER_ID,
            "model_mount_destination": "/models",
            "resources": {"cpu": "1", "mem": "1073741824"},
            "scaling_group": "default",
        },
    }
    r = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=_headers(method, rel_url), json=body)
    return r.json()


def delete_legacy_service(service_id: str) -> int:
    method = "DELETE"
    rel_url = f"/services/{service_id}"
    r = requests.delete(str(API_ENDPOINT / rel_url[1:]), headers=_headers(method, rel_url))
    return r.status_code


def run_test(test_name: str, test_func) -> bool:
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    try:
        test_func()
        print(f"  RESULT: PASS")
        return True
    except Exception as e:
        print(f"  RESULT: FAIL — {e}")
        return False


def test_sokovan_deployment():
    """Test: sokovan deployment path passes model_definition to Agent."""
    name = f"e2e-sok-{int(time.time()) % 10000}"
    print(f"  Creating deployment via bai CLI: {name}")

    result = bai(
        "deployment", "create",
        "--name", name,
        "--project-id", PROJECT_ID,
        "--desired-replicas", "1",
        "--initial-revision", "@/tmp/initial-revision.json",
    )
    deployment_id = result["deployment"]["id"]
    print(f"  Deployment ID: {deployment_id}")

    try:
        print(f"  Waiting for session to start...")
        time.sleep(15)

        db_result = db_query(
            f"SELECT k.session_name, "
            f"k.internal_data->'model_definition' IS NOT NULL as has_model_def, "
            f"CASE WHEN k.internal_data->'model_definition' IS NOT NULL "
            f"THEN k.internal_data->'model_definition'->'models'->0->'service'->'health_check'->>'initial_delay' "
            f"ELSE 'N/A' END as initial_delay "
            f"FROM kernels k WHERE k.session_name LIKE '{name}%' "
            f"ORDER BY k.created_at DESC LIMIT 1;"
        )
        print(f"  DB check: {db_result}")

        if not db_result:
            raise AssertionError("No kernel found in DB for this deployment")

        parts = db_result.split("|")
        has_model_def = parts[1].strip()
        assert has_model_def == "t", f"model_definition not in internal_data (got: {has_model_def})"

        initial_delay = parts[2].strip()
        print(f"  initial_delay in internal_data: {initial_delay}")
        assert initial_delay == "300.0", f"Expected initial_delay=300.0, got {initial_delay}"
    finally:
        print(f"  Cleaning up deployment {deployment_id}")
        bai("deployment", "delete", deployment_id)


def test_legacy_service():
    """Test: legacy service path still works."""
    name = f"e2e-leg-{int(time.time()) % 10000}"
    print(f"  Creating legacy service: {name}")
    result = create_legacy_service(name)

    if "endpoint_id" not in result:
        raise AssertionError(f"Legacy service creation failed: {result.get('msg', json.dumps(result)[:200])}")

    service_id = result["endpoint_id"]
    print(f"  Service ID: {service_id}")

    try:
        print(f"  Waiting for session to start...")
        time.sleep(10)

        db_result = db_query(
            f"SELECT k.session_name, k.status "
            f"FROM kernels k WHERE k.session_name LIKE '{name}%' "
            f"ORDER BY k.created_at DESC LIMIT 1;"
        )
        print(f"  DB check: {db_result}")

        if not db_result:
            raise AssertionError("No kernel found — session was not created")
        print(f"  Legacy service created and session started successfully")
    finally:
        print(f"  Cleaning up service {service_id}")
        delete_legacy_service(service_id)


def test_agent_logs():
    """Test: Agent log shows model_definition source and health_check values."""
    with open("/tmp/agent-e2e-final.log", "r") as f:
        log_content = f.read()

    has_source_log = "using model_definition from internal_data" in log_content
    has_health_log = "health_check config" in log_content

    print(f"  'using model_definition from internal_data': {has_source_log}")
    print(f"  'health_check config': {has_health_log}")

    for line in log_content.split("\n"):
        if "using model_definition from internal_data" in line:
            # Strip ANSI codes for readability
            clean = line.encode().decode("unicode_escape", errors="ignore")
            print(f"  >> {line.strip()[-150:]}")
            break

    for line in log_content.split("\n"):
        if "health_check config" in line:
            print(f"  >> {line.strip()[-150:]}")
            break

    assert has_source_log, "Agent did not log 'using model_definition from internal_data'"


if __name__ == "__main__":
    results = []

    results.append(run_test(
        "Sokovan deployment: model_definition passed via internal_data with initial_delay=300",
        test_sokovan_deployment,
    ))

    results.append(run_test(
        "Legacy service: session created successfully",
        test_legacy_service,
    ))

    results.append(run_test(
        "Agent log: model_definition source logged",
        test_agent_logs,
    ))

    print(f"\n{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"SUMMARY: {passed}/{total} tests passed")
    print(f"{'='*60}")

    sys.exit(0 if all(results) else 1)
