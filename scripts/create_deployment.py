#!/usr/bin/env python3
"""Create a deployment with rolling update strategy and an initial revision."""
import json
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
MODEL_VFOLDER_ID = "fb0389a96a1945bc8fb0da6e69808dea"
RESOURCE_GROUP = "default"


def call():
    method = "POST"
    rel_url = "/deployments"
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
    headers = {
        "Content-Type": content_type,
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }
    body = {
        "metadata": {
            "project_id": PROJECT_ID,
            "domain_name": DOMAIN_NAME,
            "name": "rolling-update-e2e-test",
            "tags": ["e2e-test", "rolling-update"],
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
        "initial_revision": {
            "name": "v1",
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
                "vfolder_id": MODEL_VFOLDER_ID,
                "mount_destination": "/models",
                "definition_path": "model-definition.yaml",
            },
        },
    }
    response = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=headers, json=body)
    return response.status_code, response.json()


if __name__ == "__main__":
    status_code, result = call()
    print(f"Status: {status_code}")
    print(json.dumps(result, indent=2))
