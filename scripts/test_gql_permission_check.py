#!/usr/bin/env python3
"""Test GQL queries as a regular user to check permission enforcement."""
import json
import textwrap
import requests
from datetime import datetime
from dateutil.tz import tzutc
import yarl
from ai.backend.client.auth import generate_signature

API_ENDPOINT = yarl.URL("http://127.0.0.1:8091")
API_VERSION = "v8.20240915"
HASH_TYPE = "sha256"

# Regular user credentials
USER_ACCESS_KEY = "AKIANABBDUSEREXAMPLE"
USER_SECRET_KEY = "C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf"

# Admin credentials (for comparison)
ADMIN_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
ADMIN_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

PROJECT_ID = "2de2b969-1d04-48a6-af16-0bc8adb3c831"


def send_gql(query: str, variables: dict | None, access_key: str, secret_key: str) -> dict:
    method = "POST"
    rel_url = "/admin/gql"
    date = datetime.now(tzutc())
    content_type = "application/json"
    hdrs, _ = generate_signature(
        method=method,
        version=API_VERSION,
        endpoint=API_ENDPOINT,
        date=date,
        rel_url=rel_url,
        content_type=content_type,
        access_key=access_key,
        secret_key=secret_key,
        hash_type=HASH_TYPE,
    )
    headers = {
        "Content-Type": content_type,
        "X-BackendAI-Version": API_VERSION,
        "Date": date.isoformat(),
        **hdrs,
    }
    payload: dict = {"query": query}
    if variables:
        payload["variables"] = variables
    r = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=headers, json=payload)
    return r.json()


# ── 1. ResourcePresetListQuery (resource_presets) ──
RESOURCE_PRESETS_QUERY = textwrap.dedent("""
    query {
        resource_presets {
            name
            resource_slots
            shared_memory
        }
    }
""").strip()

# ── 2. KeypairResourcePolicyListQuery (keypair_resource_policies) ──
KEYPAIR_RESOURCE_POLICIES_QUERY = textwrap.dedent("""
    query {
        keypair_resource_policies {
            name
            total_resource_slots
            max_session_lifetime
            max_concurrent_sessions
            max_containers_per_session
        }
    }
""").strip()

# ── 3. UserResourcePolicyListQuery (user_resource_policies) ──
USER_RESOURCE_POLICIES_QUERY = textwrap.dedent("""
    query {
        user_resource_policies {
            id
            name
            max_vfolder_count
            max_session_count_per_model_session
        }
    }
""").strip()

# ── 4. ImageListQuery (image_nodes with project scope) ──
IMAGE_NODES_QUERY = textwrap.dedent("""
    query($scope_id: ScopeField!) {
        image_nodes(scope_id: $scope_id) {
            count
            edges {
                node {
                    name
                    tag
                    registry
                }
            }
        }
    }
""").strip()

# ── 5. AgentListQuery (agent_nodes) ──
AGENT_NODES_QUERY = textwrap.dedent("""
    query {
        agent_nodes {
            count
            edges {
                node {
                    id
                    status
                    available_slots
                    architecture
                }
            }
        }
    }
""").strip()

# ── 6. ProjectPageQuery (group_nodes) ──
GROUP_NODES_QUERY = textwrap.dedent("""
    query {
        group_nodes {
            count
            edges {
                node {
                    id
                    name
                    domain_name
                    is_active
                }
            }
        }
    }
""").strip()


def main():
    queries = [
        ("1. ResourcePresetListQuery (resource_presets)", RESOURCE_PRESETS_QUERY, None),
        ("2. KeypairResourcePolicyListQuery (keypair_resource_policies)", KEYPAIR_RESOURCE_POLICIES_QUERY, None),
        ("3. UserResourcePolicyListQuery (user_resource_policies)", USER_RESOURCE_POLICIES_QUERY, None),
        ("4. ImageListQuery (image_nodes)", IMAGE_NODES_QUERY, {"scope_id": f"project:{PROJECT_ID}"}),
        ("5. AgentListQuery (agent_nodes)", AGENT_NODES_QUERY, None),
        ("6. ProjectPageQuery (group_nodes)", GROUP_NODES_QUERY, None),
    ]

    print("=" * 80)
    print("REGULAR USER GQL PERMISSION TEST")
    print(f"User: {USER_ACCESS_KEY}")
    print("=" * 80)

    for title, query, variables in queries:
        print(f"\n{'─' * 80}")
        print(f"  {title}")
        print(f"{'─' * 80}")
        result = send_gql(query, variables, USER_ACCESS_KEY, USER_SECRET_KEY)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Check if data was returned
        if "data" in result:
            for key, value in result["data"].items():
                if isinstance(value, list):
                    print(f"\n  >>> RESULT: {len(value)} items returned")
                elif isinstance(value, dict) and "count" in value:
                    print(f"\n  >>> RESULT: count={value['count']}, edges={len(value.get('edges', []))}")
                elif isinstance(value, dict) and "edges" in value:
                    print(f"\n  >>> RESULT: edges={len(value.get('edges', []))}")
                else:
                    print(f"\n  >>> RESULT: {type(value).__name__} returned")
        if "errors" in result:
            print(f"\n  >>> ERROR: {result['errors']}")

    # Also run as admin for comparison on resource_presets
    print(f"\n{'=' * 80}")
    print("ADMIN COMPARISON: resource_presets")
    print(f"{'=' * 80}")
    admin_result = send_gql(RESOURCE_PRESETS_QUERY, None, ADMIN_ACCESS_KEY, ADMIN_SECRET_KEY)
    print(json.dumps(admin_result, indent=2, ensure_ascii=False))
    if "data" in admin_result:
        for key, value in admin_result["data"].items():
            if isinstance(value, list):
                print(f"\n  >>> ADMIN RESULT: {len(value)} items returned")


if __name__ == "__main__":
    main()
