#!/usr/bin/env python3
"""
Rolling update E2E test: create deployment -> add revision v2 -> activate v2 (GraphQL version).
Polls deployment status until the rolling update completes or times out.
"""
import base64
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
IMAGE_ID = "4423c78d-b698-4388-b7c8-44fc52f61be1"
MODEL_VFOLDER_ID = "2c7d47fae3bd4afa841272b3da94e355"
RESOURCE_GROUP = "default"

POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 300

# ── GraphQL Queries ──

CREATE_DEPLOYMENT_MUTATION = """
mutation CreateDeployment($input: CreateDeploymentInput!) {
  createModelDeployment(input: $input) {
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
  }
}
"""

GET_DEPLOYMENT_QUERY = """
query GetDeployment($id: ID!) {
  deployment(id: $id) {
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
}
"""

ADD_REVISION_MUTATION = """
mutation AddRevision($input: AddRevisionInput!) {
  addModelRevision(input: $input) {
    revision {
      id
      name
    }
  }
}
"""

ACTIVATE_REVISION_MUTATION = """
mutation ActivateRevision($input: ActivateRevisionInput!) {
  activateDeploymentRevision(input: $input) {
    deployment {
      id
      metadata {
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

SEARCH_ROUTES_QUERY = """
query SearchRoutes($deploymentId: ID!, $first: Int, $offset: Int) {
  routes(deploymentId: $deploymentId, first: $first, offset: $offset) {
    edges {
      node {
        id
        status
        trafficStatus
        trafficRatio
        revisionId
      }
    }
    count
  }
}
"""


def make_headers():
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
    return {
        "Content-Type": content_type,
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }


def gql_request(query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    response = requests.post(
        str(API_ENDPOINT / "admin/gql/strawberry"),
        headers=make_headers(),
        json=body,
    )
    result = response.json()
    if result.get("errors"):
        print(f"  GraphQL Errors: {json.dumps(result['errors'], indent=2)}")
    return result


def make_revision_input(name, vfolder_id):
    return {
        "name": name,
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
            "vfolderId": vfolder_id,
            "mountDestination": "/models",
            "definitionPath": "model-definition.yaml",
        },
        "extraMounts": [],
    }


def decode_global_id(global_id):
    """Decode relay Global ID to raw UUID."""
    return base64.b64decode(global_id).decode().split(":")[1]


def step_create_deployment():
    print("=" * 60)
    print("[Step 1] Creating deployment with initial revision v1...")
    variables = {
        "input": {
            "metadata": {
                "projectId": PROJECT_ID,
                "domainName": DOMAIN_NAME,
                "name": f"rolling-e2e-{int(time.time())}",
                "tags": ["e2e-test", "rolling-update"],
            },
            "networkAccess": {
                "openToPublic": False,
            },
            "defaultDeploymentStrategy": {
                "type": "ROLLING",
                "rollingUpdate": {
                    "maxSurge": 1,
                    "maxUnavailable": 0,
                },
            },
            "desiredReplicaCount": 1,
            "initialRevision": make_revision_input("v1", MODEL_VFOLDER_ID),
        },
    }
    result = gql_request(CREATE_DEPLOYMENT_MUTATION, variables)
    if result.get("errors"):
        sys.exit(1)
    deployment = result["data"]["createModelDeployment"]["deployment"]
    deployment_global_id = deployment["id"]
    deployment_raw_id = decode_global_id(deployment_global_id)
    print(f"  Deployment ID (raw): {deployment_raw_id}")
    print(f"  Deployment Status: {deployment['metadata']['status']}")
    return deployment_global_id, deployment_raw_id


def step_poll_deployment_status(deployment_id, target_status, step_label):
    print(f"\n[{step_label}] Polling deployment status (target: {target_status})...")
    start_time = time.time()
    while time.time() - start_time < POLL_TIMEOUT_SECONDS:
        result = gql_request(GET_DEPLOYMENT_QUERY, {"id": deployment_id})
        deployment = result["data"]["deployment"]
        status = deployment["metadata"]["status"]
        current_revision = deployment.get("revision")
        revision_name = current_revision["name"] if current_revision else "N/A"
        elapsed = int(time.time() - start_time)
        print(f"  [{elapsed}s] status={status}, revision={revision_name}")
        if status == target_status:
            print(f"  -> Reached target status: {target_status}")
            return result
        if status in ("DESTROYED", "ERROR"):
            print(f"  -> Unexpected terminal status: {status}")
            print(f"  Full response: {json.dumps(result, indent=2)}")
            sys.exit(1)
        time.sleep(POLL_INTERVAL_SECONDS)
    print(f"  -> Timeout after {POLL_TIMEOUT_SECONDS}s")
    sys.exit(1)


def step_add_revision(deployment_raw_id):
    print("\n" + "=" * 60)
    print("[Step 3] Adding new revision v2...")
    variables = {
        "input": {
            "deploymentId": deployment_raw_id,
            **make_revision_input("v2", MODEL_VFOLDER_ID),
        },
    }
    result = gql_request(ADD_REVISION_MUTATION, variables)
    if result.get("errors"):
        sys.exit(1)
    revision = result["data"]["addModelRevision"]["revision"]
    revision_global_id = revision["id"]
    revision_raw_id = decode_global_id(revision_global_id)
    print(f"  New Revision ID (raw): {revision_raw_id}")
    return revision_raw_id


def step_activate_revision(deployment_raw_id, revision_raw_id):
    print("\n" + "=" * 60)
    print(f"[Step 4] Activating revision {revision_raw_id}...")
    variables = {
        "input": {
            "deploymentId": deployment_raw_id,
            "revisionId": revision_raw_id,
        },
    }
    result = gql_request(ACTIVATE_REVISION_MUTATION, variables)
    print(f"  Response: {json.dumps(result, indent=2)}")
    if result.get("errors"):
        sys.exit(1)
    return result


def step_check_routes(deployment_id, step_label):
    print(f"\n[{step_label}] Checking routes...")
    result = gql_request(SEARCH_ROUTES_QUERY, {
        "deploymentId": deployment_id,
        "first": 50,
        "offset": 0,
    })
    if not result.get("errors"):
        edges = result["data"]["routes"]["edges"]
        for edge in edges:
            route = edge["node"]
            print(
                f"  Route {route['id']}: "
                f"status={route['status']}, "
                f"traffic={route['trafficStatus']}, "
                f"revision={route.get('revisionId', 'N/A')}"
            )
    return result


def main():
    print("Rolling Update E2E Test (GraphQL)")
    print("=" * 60)

    # Step 1: Create deployment
    deployment_global_id, deployment_raw_id = step_create_deployment()

    # Step 2: Wait for deployment to become RUNNING (query uses Global ID)
    step_poll_deployment_status(deployment_global_id, "RUNNING", "Step 2")

    # Step 3: Add revision v2 (mutation uses raw UUID)
    revision_raw_id = step_add_revision(deployment_raw_id)

    # Step 4: Activate revision v2 (mutation uses raw UUID)
    step_activate_revision(deployment_raw_id, revision_raw_id)

    # Step 5: Poll until rolling update completes (query uses Global ID)
    final_result = step_poll_deployment_status(deployment_global_id, "RUNNING", "Step 5")

    # Step 6: Verify the current revision is v2
    current_revision = final_result["data"]["deployment"].get("revision")
    current_revision_raw_id = decode_global_id(current_revision["id"]) if current_revision else None
    if current_revision_raw_id == revision_raw_id:
        print("\n" + "=" * 60)
        print("[PASS] Rolling update completed. Current revision is v2.")
    else:
        print("\n" + "=" * 60)
        print("[FAIL] Current revision does not match the activated revision.")
        print(f"  Expected: {revision_raw_id}")
        print(f"  Got: {current_revision_raw_id}")
        sys.exit(1)

    # Step 7: Check routes (query uses Global ID)
    step_check_routes(deployment_global_id, "Step 7")

    print("\n" + "=" * 60)
    print("E2E Test Complete!")
    print(f"  Deployment ID: {deployment_raw_id}")
    print(f"  Final Revision ID: {revision_raw_id}")


if __name__ == "__main__":
    main()
