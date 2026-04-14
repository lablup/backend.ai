#!/usr/bin/env python3
"""Verify session_pending_queue permission fix."""
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


QUERY = textwrap.dedent("""
    query {
        session_pending_queue(resource_group_id: "default", first: 10) {
            count
            edges { node { row_id status } }
        }
    }
""").strip()

print("=" * 60)
print("TEST 1: session_pending_queue as regular user")
print("=" * 60)
result = send_gql(QUERY, None, USER_ACCESS_KEY, USER_SECRET_KEY)
print(json.dumps(result, indent=2))
if result.get("errors"):
    print(">>> PASS: Permission denied")
else:
    print(">>> FAIL: Data returned")

print("\n" + "=" * 60)
print("TEST 2: session_pending_queue as admin")
print("=" * 60)
result = send_gql(QUERY, None, ADMIN_ACCESS_KEY, ADMIN_SECRET_KEY)
print(json.dumps(result, indent=2))
if result.get("errors") and "Forbidden" in str(result["errors"]):
    print(">>> FAIL: Admin blocked")
elif result.get("data"):
    print(">>> PASS: Admin can access")
else:
    print(">>> Result:", result)
