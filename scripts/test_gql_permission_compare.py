#!/usr/bin/env python3
"""Compare admin vs regular user GQL results for key queries."""
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

USER_ACCESS_KEY = "AKIANABBDUSEREXAMPLE"
USER_SECRET_KEY = "C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf"
ADMIN_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
ADMIN_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
PROJECT_ID = "2de2b969-1d04-48a6-af16-0bc8adb3c831"


def send_gql(query, variables, access_key, secret_key):
    method = "POST"
    rel_url = "/admin/gql"
    date = datetime.now(tzutc())
    content_type = "application/json"
    hdrs, _ = generate_signature(
        method=method, version=API_VERSION, endpoint=API_ENDPOINT,
        date=date, rel_url=rel_url, content_type=content_type,
        access_key=access_key, secret_key=secret_key, hash_type=HASH_TYPE,
    )
    headers = {"Content-Type": content_type, "X-BackendAI-Version": API_VERSION,
               "Date": date.isoformat(), **hdrs}
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    r = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=headers, json=payload)
    return r.json()


def compare(title, query, variables=None):
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")

    admin_result = send_gql(query, variables, ADMIN_ACCESS_KEY, ADMIN_SECRET_KEY)
    user_result = send_gql(query, variables, USER_ACCESS_KEY, USER_SECRET_KEY)

    for key in (admin_result.get("data") or {}):
        admin_data = admin_result["data"][key]
        user_data = user_result["data"][key]

        if isinstance(admin_data, list):
            admin_count = len(admin_data)
            user_count = len(user_data)
        elif isinstance(admin_data, dict) and "count" in admin_data:
            admin_count = admin_data["count"]
            user_count = user_data["count"]
        else:
            admin_count = "?"
            user_count = "?"

        print(f"\n  Admin: {admin_count} items")
        print(f"  User:  {user_count} items")
        if admin_count == user_count:
            print(f"  >>> SAME DATA RETURNED — potential issue!")
        else:
            print(f"  >>> Different counts — filtering is working")

    print(f"\n  [Admin Response]")
    print(json.dumps(admin_result, indent=2, ensure_ascii=False)[:2000])
    print(f"\n  [User Response]")
    print(json.dumps(user_result, indent=2, ensure_ascii=False)[:2000])


# ── image_nodes ──
compare(
    "image_nodes (project scope)",
    textwrap.dedent("""
        query($scope_id: ScopeField!) {
            image_nodes(scope_id: $scope_id, first: 3) {
                count
                edges { node { name tag registry } }
            }
        }
    """).strip(),
    {"scope_id": f"project:{PROJECT_ID}"},
)

# ── agent_nodes ──
compare(
    "agent_nodes (default SystemScope)",
    textwrap.dedent("""
        query {
            agent_nodes {
                count
                edges { node { id status available_slots occupied_slots architecture addr } }
            }
        }
    """).strip(),
)

# ── agent_nodes with more sensitive fields ──
compare(
    "agent_nodes (with sensitive fields)",
    textwrap.dedent("""
        query {
            agent_nodes {
                count
                edges { node { id status addr scaling_group region } }
            }
        }
    """).strip(),
)

# ── group_nodes ──
compare(
    "group_nodes",
    textwrap.dedent("""
        query {
            group_nodes {
                count
                edges { node { id name domain_name is_active } }
            }
        }
    """).strip(),
)

# ── keypair_resource_policies (admin sees more?) ──
compare(
    "keypair_resource_policies",
    textwrap.dedent("""
        query {
            keypair_resource_policies {
                name
                total_resource_slots
                max_concurrent_sessions
                max_containers_per_session
            }
        }
    """).strip(),
)
