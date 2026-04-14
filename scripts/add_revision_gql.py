#!/usr/bin/env python3
"""Add a new revision (v2) to an existing deployment (GraphQL version)."""
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
DEPLOYMENT_ID = "5d94e1a4-c238-4d29-b0fb-4a4f782cf5e9"
IMAGE_ID = "4423c78d-b698-4388-b7c8-44fc52f61be1"
MODEL_VFOLDER_ID = "fb0389a96a1945bc8fb0da6e69808dea"
RESOURCE_GROUP = "default"

QUERY = """
mutation AddRevision($input: AddRevisionInput!) {
  addModelRevision(input: $input) {
    revision {
      id
      name
      createdAt
    }
  }
}
"""


def call():
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
    headers = {
        "Content-Type": content_type,
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }
    variables = {
        "input": {
            "deploymentId": DEPLOYMENT_ID,
            "name": "v2",
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
                "vfolderId": MODEL_VFOLDER_ID,
                "mountDestination": "/models",
                "definitionPath": "model-definition.yaml",
            },
        },
    }
    body = {"query": QUERY, "variables": variables}
    response = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=headers, json=body)
    return response.status_code, response.json()


if __name__ == "__main__":
    status_code, result = call()
    print(f"Status: {status_code}")
    print(json.dumps(result, indent=2))
