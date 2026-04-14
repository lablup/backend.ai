#!/usr/bin/env python3
"""E2E test: verify Agent receives Manager-merged model_definition with custom health_check."""
import json
import textwrap
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
VFOLDER_ID = "78116ee1-ed50-4f1c-b513-7cf46f21a3a1"
IMAGE = "cr.backend.ai/stable/python:3.9-ubuntu20.04"


def _headers(method, rel_url):
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


def create_service():
    """Create a model service with custom runtime variant."""
    method = "POST"
    rel_url = "/services"
    body = {
        "service_name": f"hc-test-{int(time.time()) % 100000}",
        "model": VFOLDER_ID,
        "model_definition_path": "model-definition.yaml",
        "image": IMAGE,
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
    headers = _headers(method, rel_url)
    r = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=headers, json=body)
    return r.json()


def get_service(service_id):
    """Get service status."""
    method = "GET"
    rel_url = f"/services/{service_id}"
    headers = _headers(method, rel_url)
    r = requests.get(str(API_ENDPOINT / rel_url[1:]), headers=headers)
    return r.json()


def delete_service(service_id):
    """Delete (terminate) a service."""
    method = "DELETE"
    rel_url = f"/services/{service_id}"
    headers = _headers(method, rel_url)
    r = requests.delete(str(API_ENDPOINT / rel_url[1:]), headers=headers)
    return r.status_code


if __name__ == "__main__":
    print("=== Creating model service with custom health_check override ===")
    result = create_service()
    print(json.dumps(result, indent=2))

    if "endpoint_id" in result:
        service_id = result["endpoint_id"]
        print(f"\nService created: {service_id}")
        print("Waiting 10s for session to start...")
        time.sleep(10)

        print("\n=== Service status ===")
        status = get_service(service_id)
        print(json.dumps(status, indent=2))

        print(f"\n>>> Now check Agent log for 'model definition loaded' to verify health_check values.")
        print(f">>> Expected: initial_delay=300, max_retries=30, max_wait_time=20")
        print(f">>> Run: grep 'model definition loaded' /tmp/agent-startup.log")

        print(f"\n=== Cleaning up: deleting service {service_id} ===")
        code = delete_service(service_id)
        print(f"Delete status: {code}")
    else:
        print("ERROR: Service creation failed")
