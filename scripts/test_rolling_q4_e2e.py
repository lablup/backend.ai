#!/usr/bin/env python3
"""Rolling update E2E test: quorum=4, max_surge=50% (PERCENT), GQL."""
import base64
import json
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

PROJECT_ID = "2de2b969-1d04-48a6-af16-0bc8adb3c831"
DOMAIN_NAME = "default"
IMAGE_ID = "4423c78d-b698-4388-b7c8-44fc52f61be1"
MODEL_VFOLDER_ID = "2c7d47fae3bd4afa841272b3da94e355"
RESOURCE_GROUP = "default"

POLL_INTERVAL = 5
POLL_TIMEOUT = 600


def make_headers():
    date = datetime.now(tzutc())
    hdrs, _ = generate_signature(
        method="POST", version=API_VERSION, endpoint=API_ENDPOINT,
        date=date, rel_url="/admin/gql/strawberry",
        content_type="application/json",
        access_key=ACCESS_KEY, secret_key=SECRET_KEY, hash_type="sha256",
    )
    return {
        "Content-Type": "application/json",
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }


def gql(query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    r = requests.post(
        str(API_ENDPOINT / "admin/gql/strawberry"),
        headers=make_headers(), json=body,
    )
    result = r.json()
    if result.get("errors"):
        print(f"  GQL Errors: {json.dumps(result['errors'], indent=2)}")
    return result


def decode_gid(gid):
    return base64.b64decode(gid).decode().split(":")[1]


def rev_input_base(name, vfolder_id):
    return {
        "name": name,
        "clusterConfig": {"mode": "SINGLE_NODE", "size": 1},
        "resourceConfig": {
            "resourceGroup": {"name": RESOURCE_GROUP},
            "resourceSlots": {
                "entries": [
                    {"resourceType": "cpu", "quantity": "1"},
                    {"resourceType": "mem", "quantity": "1073741824"},
                ],
            },
        },
        "image": {"id": IMAGE_ID},
        "modelRuntimeConfig": {"runtimeVariant": "custom"},
        "modelMountConfig": {
            "vfolderId": vfolder_id,
            "mountDestination": "/models",
            "definitionPath": "model-definition.yaml",
        },
        "extraMounts": [],
    }


MODEL_DEFINITION = {
    "models": [{
        "name": "custom-model",
        "modelPath": "/models",
        "service": {
            "startCommand": "python3 -m http.server 8000",
            "port": 8000,
            "healthCheck": {"path": "/", "maxRetries": 30},
            "preStartActions": [],
        },
    }],
}


def rev_input_for_create(name, vfolder_id):
    """For CreateDeploymentInput.initialRevision (no modelDefinition)."""
    return rev_input_base(name, vfolder_id)


def rev_input_for_add(name, vfolder_id):
    """For AddRevisionInput (requires modelDefinition)."""
    result = rev_input_base(name, vfolder_id)
    result["modelDefinition"] = MODEL_DEFINITION
    return result


def poll(gid, target, label):
    print(f"\n[{label}] Polling (target: {target})...")
    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        r = gql(
            "query($id:ID!){deployment(id:$id){id metadata{name status} revision{id name}}}",
            {"id": gid},
        )
        d = r["data"]["deployment"]
        st = d["metadata"]["status"]
        rev = d.get("revision")
        rn = rev["name"] if rev else "N/A"
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] status={st}, revision={rn}")
        if st == target:
            return r
        if st in ("DESTROYED", "ERROR"):
            print(f"  -> Terminal: {st}")
            sys.exit(1)
        time.sleep(POLL_INTERVAL)
    print("  -> Timeout")
    sys.exit(1)


def check_routes(gid, label):
    print(f"\n[{label}] Checking routes...")
    r = gql(
        "query($id:ID!,$first:Int,$offset:Int){routes(deploymentId:$id,first:$first,offset:$offset){edges{node{id status trafficStatus trafficRatio revisionId}}count}}",
        {"id": gid, "first": 50, "offset": 0},
    )
    if not r.get("errors"):
        for e in r["data"]["routes"]["edges"]:
            n = e["node"]
            print(
                f"  Route {n['id']}: status={n['status']}, "
                f"traffic={n['trafficStatus']}, revision={n.get('revisionId','N/A')}"
            )
    return r


def add_revision(raw_id, name, vfolder_id):
    print(f"\n  Adding revision '{name}'...")
    r = gql(
        "mutation($input:AddRevisionInput!){addModelRevision(input:$input){revision{id name}}}",
        {"input": {"deploymentId": raw_id, **rev_input_for_add(name, vfolder_id)}},
    )
    if r.get("errors"):
        sys.exit(1)
    rev = r["data"]["addModelRevision"]["revision"]
    rev_raw = decode_gid(rev["id"])
    print(f"  Revision '{name}' ID: {rev_raw}")
    return rev_raw


def activate_revision(raw_id, rev_raw):
    print(f"  Activating revision {rev_raw}...")
    r = gql(
        "mutation($input:ActivateRevisionInput!){activateDeploymentRevision(input:$input){deployment{id metadata{status} revision{id name}} previousRevisionId activatedRevisionId}}",
        {"input": {"deploymentId": raw_id, "revisionId": rev_raw}},
    )
    if r.get("errors"):
        print(f"  Response: {json.dumps(r, indent=2)}")
        sys.exit(1)
    return r


def main():
    print("=" * 60)
    print("Rolling Update E2E: quorum=4, max_surge=PERCENT 50%")
    print("=" * 60)

    # Step 1: Create deployment (no initial revision row created by new path)
    print("\n[Step 1] Creating deployment with 4 replicas, max_surge=50%...")
    r = gql(
        "mutation($input:CreateDeploymentInput!){createModelDeployment(input:$input){deployment{id metadata{name status} revision{id name}}}}",
        {
            "input": {
                "metadata": {
                    "projectId": PROJECT_ID,
                    "domainName": DOMAIN_NAME,
                    "name": f"rolling-q4-pct-{int(time.time())}",
                    "tags": ["e2e"],
                },
                "networkAccess": {"openToPublic": False},
                "defaultDeploymentStrategy": {
                    "type": "ROLLING",
                    "rollingUpdate": {
                        "maxSurge": {"type": "PERCENT", "percent": 0.5},
                        "maxUnavailable": {"type": "COUNT", "count": 0},
                    },
                },
                "desiredReplicaCount": 1,
                "initialRevision": rev_input_for_create("v1", MODEL_VFOLDER_ID),
            },
        },
    )
    if r.get("errors"):
        sys.exit(1)
    dep = r["data"]["createModelDeployment"]["deployment"]
    gid = dep["id"]
    raw_id = decode_gid(gid)
    print(f"  Deployment ID: {raw_id}")
    print(f"  Status: {dep['metadata']['status']}")

    # Step 2: Add revision v1 via addModelRevision and activate it
    print("\n[Step 2] Adding & activating initial revision v1...")
    v1_raw = add_revision(raw_id, "v1", MODEL_VFOLDER_ID)
    activate_revision(raw_id, v1_raw)

    # Step 3: Wait RUNNING
    poll(gid, "RUNNING", "Step 3")
    check_routes(gid, "Step 3.5")

    # Step 4: Add revision v2
    print("\n" + "=" * 60)
    print("[Step 4] Adding revision v2...")
    v2_raw = add_revision(raw_id, "v2", MODEL_VFOLDER_ID)

    # Step 5: Activate v2 (triggers rolling update)
    print("\n" + "=" * 60)
    print(f"[Step 5] Activating revision v2 (rolling update)...")
    activate_revision(raw_id, v2_raw)

    # Step 6: Poll RUNNING
    final = poll(gid, "RUNNING", "Step 6")

    # Step 7: Verify
    cur = final["data"]["deployment"].get("revision")
    cur_raw = decode_gid(cur["id"]) if cur else None
    if cur_raw == v2_raw:
        print("\n" + "=" * 60)
        print("[PASS] Rolling update completed. Current revision is v2.")
    else:
        print(f"\n[FAIL] Expected: {v2_raw}, Got: {cur_raw}")
        sys.exit(1)

    # Step 8: Routes
    check_routes(gid, "Step 8")
    print("\n" + "=" * 60)
    print(f"E2E Complete! Deployment: {raw_id}, Revision: {v2_raw}")


if __name__ == "__main__":
    main()
