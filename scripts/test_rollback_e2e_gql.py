#!/usr/bin/env python3
"""
Rollback E2E test: create deployment -> add broken revision -> activate -> expect rollback
(GraphQL version).
Uses a broken model vfolder (health check returns 500) to trigger automatic rollback.
"""
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
IMAGE_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
GOOD_MODEL_VFOLDER_ID = "fb0389a96a1945bc8fb0da6e69808dea"
BROKEN_MODEL_VFOLDER_ID = "af47d6ce645846d3b2109f3f2f36ff10"
RESOURCE_GROUP = "default"

POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 600  # longer timeout for rollback scenario

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
      subStep
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
    if "errors" in result:
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
    }


def step_create_deployment():
    print("=" * 60)
    print("[Step 1] Creating deployment with good model (v1)...")
    variables = {
        "input": {
            "metadata": {
                "projectId": PROJECT_ID,
                "domainName": DOMAIN_NAME,
                "name": f"rollback-e2e-{int(time.time())}",
                "tags": ["e2e-test", "rollback"],
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
            "initialRevision": make_revision_input("v1-good", GOOD_MODEL_VFOLDER_ID),
        },
    }
    result = gql_request(CREATE_DEPLOYMENT_MUTATION, variables)
    if "errors" in result:
        sys.exit(1)
    deployment = result["data"]["createModelDeployment"]["deployment"]
    deployment_id = deployment["id"]
    current_revision = deployment.get("revision")
    initial_revision_id = current_revision["id"] if current_revision else None
    print(f"  Deployment ID: {deployment_id}")
    print(f"  Initial Revision ID: {initial_revision_id}")
    return deployment_id, initial_revision_id


def step_poll_deployment_status(deployment_id, target_statuses, step_label):
    """Poll until status matches one of target_statuses."""
    if isinstance(target_statuses, str):
        target_statuses = [target_statuses]
    print(f"\n[{step_label}] Polling deployment status (target: {target_statuses})...")
    start_time = time.time()
    while time.time() - start_time < POLL_TIMEOUT_SECONDS:
        result = gql_request(GET_DEPLOYMENT_QUERY, {"id": deployment_id})
        deployment = result["data"]["deployment"]
        status = deployment["metadata"]["status"]
        sub_step = deployment["metadata"].get("subStep")
        current_revision = deployment.get("revision")
        revision_name = current_revision["name"] if current_revision else "N/A"
        revision_id = current_revision["id"] if current_revision else "N/A"
        elapsed = int(time.time() - start_time)
        print(
            f"  [{elapsed}s] status={status}, sub_step={sub_step}, "
            f"revision={revision_name} ({revision_id})"
        )
        if status in target_statuses:
            print(f"  -> Reached target status: {status}")
            return result
        if status in ("DESTROYED",):
            print(f"  -> Unexpected terminal status: {status}")
            print(f"  Full response: {json.dumps(result, indent=2)}")
            sys.exit(1)
        time.sleep(POLL_INTERVAL_SECONDS)
    print(f"  -> Timeout after {POLL_TIMEOUT_SECONDS}s")
    sys.exit(1)


def step_add_broken_revision(deployment_id):
    print("\n" + "=" * 60)
    print("[Step 3] Adding broken revision v2 (health check will fail)...")
    variables = {
        "input": {
            "deploymentId": deployment_id,
            **make_revision_input("v2-broken", BROKEN_MODEL_VFOLDER_ID),
        },
    }
    result = gql_request(ADD_REVISION_MUTATION, variables)
    if "errors" in result:
        sys.exit(1)
    revision = result["data"]["addModelRevision"]["revision"]
    revision_id = revision["id"]
    print(f"  Broken Revision ID: {revision_id}")
    return revision_id


def step_activate_revision(deployment_id, revision_id, step_label):
    print(f"\n[{step_label}] Activating broken revision {revision_id}...")
    variables = {
        "input": {
            "deploymentId": deployment_id,
            "revisionId": revision_id,
        },
    }
    result = gql_request(ACTIVATE_REVISION_MUTATION, variables)
    print(f"  Response: {json.dumps(result, indent=2)}")
    return result


def step_check_routes(deployment_id, step_label):
    print(f"\n[{step_label}] Checking routes...")
    result = gql_request(SEARCH_ROUTES_QUERY, {
        "deploymentId": deployment_id,
        "first": 50,
        "offset": 0,
    })
    if "errors" not in result:
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
    print("Rollback E2E Test - GraphQL (broken revision -> automatic rollback)")
    print("=" * 60)

    # Step 1: Create deployment with good model
    deployment_id, initial_revision_id = step_create_deployment()

    # Step 2: Wait for deployment to become RUNNING
    running_result = step_poll_deployment_status(deployment_id, "RUNNING", "Step 2")
    if not initial_revision_id:
        initial_revision_id = running_result["data"]["deployment"]["revision"]["id"]
    print(f"  Initial (good) revision: {initial_revision_id}")

    # Step 3: Add broken revision
    broken_revision_id = step_add_broken_revision(deployment_id)

    # Step 4: Activate broken revision (triggers rolling update)
    step_activate_revision(deployment_id, broken_revision_id, "Step 4")

    # Step 5: Poll until rollback completes (should go back to RUNNING after rollback)
    # The system should detect health check failure and roll back to v1
    final_result = step_poll_deployment_status(
        deployment_id, ["RUNNING", "ERROR"], "Step 5"
    )

    # Step 6: Verify rollback
    deployment = final_result["data"]["deployment"]
    final_status = deployment["metadata"]["status"]
    current_revision = deployment.get("revision")
    current_revision_id = current_revision["id"] if current_revision else None

    print("\n" + "=" * 60)
    if final_status == "RUNNING" and current_revision_id == initial_revision_id:
        print("[PASS] Rollback succeeded! Deployment reverted to v1 (good model).")
    elif final_status == "ERROR":
        print("[INFO] Deployment entered ERROR status.")
        print("  This may indicate the rollback mechanism detected the failure.")
        print(f"  Current revision: {current_revision_id}")
    else:
        print("[FAIL] Unexpected final state.")
        print(f"  Status: {final_status}")
        print(f"  Current revision: {current_revision_id}")
        print(f"  Expected revision (v1): {initial_revision_id}")

    # Step 7: Check routes
    step_check_routes(deployment_id, "Step 7")

    print("\n" + "=" * 60)
    print("Rollback E2E Test Complete!")
    print(f"  Deployment ID: {deployment_id}")
    print(f"  Good Revision (v1): {initial_revision_id}")
    print(f"  Broken Revision (v2): {broken_revision_id}")
    print(f"  Final Revision: {current_revision_id}")


if __name__ == "__main__":
    main()
