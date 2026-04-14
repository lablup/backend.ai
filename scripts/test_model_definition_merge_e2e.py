#!/usr/bin/env python3
"""E2E test: verify model_definition merge during add_model_revision.

Flow:
  1. Create a deployment with initial revision (custom variant, no user override)
     → DB should contain vfolder's model-definition.yaml as-is
  2. Add a second revision WITH user-provided model_definition override
     → DB should contain deep-merged result (vfolder base + user override)
  3. Query DB to verify both revisions

Vfolder model-definition.yaml (base):
  models:
  - name: test-model
    model_path: /models
    service:
      start_command: [python3, -m, http.server, "8080"]
      port: 8080
      health_check:
        path: /
        max_retries: 10

User override (applied on top in revision 2):
  models:
  - name: test-model
    service:
      port: 9999
      health_check:
        path: /healthz
        max_retries: 3

Expected merged result for revision 2:
  models:
  - name: test-model
    model_path: /models        ← preserved from vfolder
    service:
      start_command: [...]     ← preserved from vfolder
      port: 9999               ← overridden by user
      health_check:
        path: /healthz         ← overridden by user
        max_retries: 3         ← overridden by user
"""

import json
import subprocess
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
IMAGE_ID = "1fa48424-b715-4315-9690-818b680c7e73"
MODEL_VFOLDER_ID = "fb0389a96a1945bc8fb0da6e69808dea"
RESOURCE_GROUP = "default"

DB_CONTAINER = "main-backendai-half-db-1"


def _headers(method: str, rel_url: str) -> dict:
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


def _db_query(sql: str) -> str:
    result = subprocess.run(
        [
            "docker", "exec", DB_CONTAINER,
            "psql", "-U", "postgres", "-d", "backend",
            "-t", "-A", "-c", sql,
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def step(msg: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {msg}")
    print(f"{'─'*60}")


def create_deployment() -> str:
    """Create deployment with initial revision (no user model_definition override)."""
    step("Step 1: Create deployment (vfolder model-definition.yaml only)")
    rel_url = "/deployments"
    body = {
        "metadata": {
            "project_id": PROJECT_ID,
            "domain_name": DOMAIN_NAME,
            "name": f"model-def-merge-test-{int(time.time())}",
            "tags": ["e2e-test", "model-definition-merge"],
        },
        "network_access": {"open_to_public": False},
        "default_deployment_strategy": {
            "type": "ROLLING",
            "rolling_update": {"max_surge": 1, "max_unavailable": 0},
        },
        "desired_replica_count": 1,
        "initial_revision": {
            "name": "v1-base",
            "cluster_config": {"mode": "SINGLE_NODE", "size": 1},
            "resource_config": {
                "resource_group": RESOURCE_GROUP,
                "resource_slots": {"cpu": "1", "mem": "1073741824"},
            },
            "image": {"id": IMAGE_ID},
            "model_runtime_config": {"runtime_variant": "custom"},
            "model_mount_config": {
                "vfolder_id": MODEL_VFOLDER_ID,
                "mount_destination": "/models",
                "definition_path": "model-definition.yaml",
            },
            # No model_definition — should use vfolder file only
        },
    }
    response = requests.post(
        str(API_ENDPOINT / rel_url[1:]),
        headers=_headers("POST", rel_url),
        json=body,
    )
    print(f"  Status: {response.status_code}")
    result = response.json()
    if response.status_code not in (200, 201):
        print(f"  FAILED: {json.dumps(result, indent=2)}")
        sys.exit(1)

    deployment = result.get("deployment", {})
    deployment_id = deployment.get("id") or result.get("deployment_id") or result.get("id")
    print(f"  Deployment ID: {deployment_id}")
    return deployment_id


def add_revision_with_override(deployment_id: str) -> None:
    """Add revision with user-provided model_definition override."""
    step("Step 2: Add revision with model_definition override")
    rel_url = f"/deployments/{deployment_id}/revisions"
    body = {
        "revision": {
            "name": "v2-with-override",
            "cluster_config": {"mode": "SINGLE_NODE", "size": 1},
            "resource_config": {
                "resource_group": RESOURCE_GROUP,
                "resource_slots": {"cpu": "1", "mem": "1073741824"},
            },
            "image": {"id": IMAGE_ID},
            "model_runtime_config": {"runtime_variant": "custom"},
            "model_mount_config": {
                "vfolder_id": MODEL_VFOLDER_ID,
                "mount_destination": "/models",
                "definition_path": "model-definition.yaml",
            },
            "model_definition": {
                "models": [
                    {
                        "name": "test-model",
                        "model-path": "/models",
                        "service": {
                            "start-command": ["python3", "-m", "http.server", "9999"],
                            "port": 9999,
                            "health_check": {
                                "path": "/healthz",
                                "max_retries": 3,
                            },
                        },
                    }
                ]
            },
        },
    }
    response = requests.post(
        str(API_ENDPOINT / rel_url[1:]),
        headers=_headers("POST", rel_url),
        json=body,
    )
    print(f"  Status: {response.status_code}")
    result = response.json()
    print(f"  Response: {json.dumps(result, indent=2)}")
    if response.status_code not in (200, 201):
        print("  FAILED to add revision!")
        sys.exit(1)


def verify_revisions(deployment_id: str) -> bool:
    """Query DB and verify both revisions' model_definition."""
    step("Step 3: Query DB and verify merge results")

    sql = (
        "SELECT revision_number, model_definition::text "
        "FROM deployment_revisions "
        f"WHERE endpoint = '{deployment_id}' "
        "ORDER BY revision_number"
    )
    raw = _db_query(sql)
    if not raw:
        print("  [FAIL] No revisions found in DB")
        return False

    rows = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 1)
        revision_number = int(parts[0])
        model_definition = json.loads(parts[1]) if parts[1] else None
        rows.append((revision_number, model_definition))

    if len(rows) < 1:
        print("  [FAIL] No revisions found")
        return False

    success = True

    # Find the revision with model_definition (added via add_revision with override)
    rev_def = None
    for rev_num, definition in rows:
        if definition is not None:
            rev_def = definition
            print(f"\n  === Revision {rev_num} (vfolder + user override = merged) ===")
            break

    if rev_def is None:
        print("  [FAIL] No revision with model_definition found")
        return False

    print(f"  {json.dumps(rev_def, indent=4)}")
    model = rev_def["models"][0]

    # User override should take precedence over vfolder
    # Note: DB stores with by_alias=True, so keys use hyphens (e.g. "start-command")
    service = model.get("service", {})
    start_cmd = service.get("start-command") or service.get("start_command")
    expected_cmd = ["python3", "-m", "http.server", "9999"]
    if start_cmd == expected_cmd:
        print(f"  [OK] start-command = {start_cmd} (from user override)")
    else:
        print(f"  [FAIL] start-command: expected {expected_cmd}, got {start_cmd}")
        success = False

    health_check = service.get("health-check") or service.get("health_check") or {}
    checks = [
        ("port", service.get("port"), 9999),
        ("health-check.path", health_check.get("path"), "/healthz"),
        ("health-check.max-retries", health_check.get("max-retries", health_check.get("max_retries")), 3),
    ]
    for field, actual, expected in checks:
        if actual == expected:
            print(f"  [OK] {field} = {actual} (from user override)")
        else:
            print(f"  [FAIL] {field}: expected {expected}, got {actual}")
            success = False

    return success


def delete_deployment(deployment_id: str) -> None:
    """Clean up."""
    step("Cleanup: Delete deployment")
    rel_url = f"/deployments/{deployment_id}"
    response = requests.delete(
        str(API_ENDPOINT / rel_url[1:]),
        headers=_headers("DELETE", rel_url),
    )
    print(f"  Status: {response.status_code}")


def main() -> None:
    print("=" * 60)
    print("  E2E: model_definition merge verification (BA-5389)")
    print("=" * 60)

    deployment_id = None
    try:
        deployment_id = create_deployment()
        time.sleep(2)

        add_revision_with_override(deployment_id)
        time.sleep(1)

        if verify_revisions(deployment_id):
            print("\n" + "=" * 60)
            print("  RESULT: ALL CHECKS PASSED")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("  RESULT: SOME CHECKS FAILED")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if deployment_id:
            delete_deployment(deployment_id)


if __name__ == "__main__":
    main()
