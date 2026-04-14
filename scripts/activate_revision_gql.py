#!/usr/bin/env python3
"""Activate a specific revision on a deployment, triggering rolling update (GraphQL version)."""
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
REVISION_ID = "deb2d344-1983-4348-a816-d430c5c8b527"

QUERY = """
mutation ActivateRevision($input: ActivateRevisionInput!) {
  activateDeploymentRevision(input: $input) {
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
    }
    previousRevisionId
    activatedRevisionId
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
            "revisionId": REVISION_ID,
        },
    }
    body = {"query": QUERY, "variables": variables}
    response = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=headers, json=body)
    return response.status_code, response.json()


if __name__ == "__main__":
    status_code, result = call()
    print(f"Status: {status_code}")
    print(json.dumps(result, indent=2))
