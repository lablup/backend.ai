#!/usr/bin/env python3
"""Verify resource_presets permission fix."""
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


PRESETS_QUERY = textwrap.dedent("""
    query { resource_presets { name resource_slots } }
""").strip()

PRESET_BY_NAME_QUERY = textwrap.dedent("""
    query { resource_preset(name: "cpu01-small") { name resource_slots } }
""").strip()

print("=" * 60)
print("TEST 1: resource_presets (list) as regular user")
print("=" * 60)
result = send_gql(PRESETS_QUERY, None, USER_ACCESS_KEY, USER_SECRET_KEY)
print(json.dumps(result, indent=2))
if result.get("errors"):
    print(">>> PASS: Permission denied for regular user")
else:
    print(">>> FAIL: Data returned to regular user")

print("\n" + "=" * 60)
print("TEST 2: resource_preset (by name) as regular user")
print("=" * 60)
result = send_gql(PRESET_BY_NAME_QUERY, None, USER_ACCESS_KEY, USER_SECRET_KEY)
print(json.dumps(result, indent=2))
if result.get("errors"):
    print(">>> PASS: Permission denied for regular user")
else:
    print(">>> FAIL: Data returned to regular user")

print("\n" + "=" * 60)
print("TEST 3: resource_presets (list) as admin")
print("=" * 60)
result = send_gql(PRESETS_QUERY, None, ADMIN_ACCESS_KEY, ADMIN_SECRET_KEY)
print(json.dumps(result, indent=2))
if result.get("data", {}).get("resource_presets"):
    print(f">>> PASS: Admin sees {len(result['data']['resource_presets'])} presets")
else:
    print(">>> FAIL: Admin cannot see presets")
