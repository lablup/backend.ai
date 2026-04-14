"""
BA-5608 Issue #1: Scaling group access error reproduction.

Setup (run scripts/setup_scaling_group_repro.sql first):
- 'restricted-sg' scaling group exists
- Only admin's keypair (AKIAIOSFODNN7EXAMPLE) is associated with it
- user@lablup.com's keypair has NO access to it via any path

Tests:
- Test A: Admin creates own session in 'restricted-sg' → SUCCESS
- Test B: Admin creates session with owner_access_key=user@lablup.com in 'restricted-sg'
         → "Scaling group 'restricted-sg' is not accessible"

Note: This is technically the EXPECTED behavior — if the owner doesn't actually have
access, the request should fail. The production complaint of "실제 권한이 있어도
접근이 안되는" likely indicates either:
  (a) The owner had keypair-level access on a DIFFERENT keypair (admin granted it
      to the wrong AK), or
  (b) The owner had access via a group that didn't get resolved correctly somewhere.
The user_uuid bug (Scenario A in the investigation doc) is the clear, reproducible
half. Issue #1 needs the original reporter's exact env to fully diagnose.
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone

import requests

ENDPOINT = "http://127.0.0.1:8091"
API_VERSION = "v9.20250722"

ADMIN_AK = "AKIAIOSFODNN7EXAMPLE"
ADMIN_SK = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
USER_AK = "AKIANABBDUSEREXAMPLE"


def call(access_key, secret_key, method, uri, body_dict, label):
    now = datetime.now(timezone.utc)
    raw_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_key = now.strftime("%Y%m%d")
    body_text = json.dumps(body_dict)
    body_hash = hashlib.sha256(b"").hexdigest()
    host = "127.0.0.1:8091"

    sk = hmac.new(secret_key.encode(), date_key.encode(), hashlib.sha256).digest()
    sk = hmac.new(sk, host.encode(), hashlib.sha256).digest()
    ss = (
        f"{method}\n{uri}\n{raw_date}\n"
        f"host:{host}\n"
        f"content-type:application/json\n"
        f"x-backendai-version:{API_VERSION}\n"
        f"{body_hash}"
    )
    sig = hmac.new(sk, ss.encode(), hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-BackendAI-Version": API_VERSION,
        "X-BackendAI-Date": raw_date,
        "Authorization": f"BackendAI signMethod=HMAC-SHA256, credential={access_key}:{sig}",
    }

    print(f"\n{'=' * 60}\n[{label}]")
    if "owner_access_key" in body_dict:
        print(f"  owner_access_key: {body_dict['owner_access_key']}")
    print(f"  scaling_group: {body_dict.get('config', {}).get('scaling_group', '?')}")

    resp = requests.request(method, f"{ENDPOINT}{uri}", headers=headers, data=body_text)
    print(f"  status: {resp.status_code}")
    try:
        result = resp.json()
        if resp.status_code >= 400:
            print(f"  error: {result.get('msg', result.get('title', '?'))}")
        else:
            print(f"  sessionId: {result.get('sessionId', '?')}")
    except Exception:
        print(f"  body: {resp.text[:300]}")
    return resp


SCALING_GROUP = "restricted-sg"
ts = datetime.now(timezone.utc).strftime("%H%M%S")

base_body = {
    "image": "cr.backend.ai/stable/python:3.9-ubuntu22.04-amd64",
    "domain": "default",
    "group_name": "default",
    "enqueueOnly": True,
    "config": {
        "resources": {"cpu": 1, "mem": "512m"},
        "scaling_group": SCALING_GROUP,
    },
}

# Test A: admin's own session
resp_a = call(
    ADMIN_AK,
    ADMIN_SK,
    "POST",
    "/session",
    {**base_body, "clientSessionToken": f"sg-test-admin-{ts}"},
    "A: Admin's own session in restricted-sg (expect SUCCESS)",
)

# Test B: admin acting on behalf of user
resp_b = call(
    ADMIN_AK,
    ADMIN_SK,
    "POST",
    "/session",
    {
        **base_body,
        "clientSessionToken": f"sg-test-deleg-{ts}",
        "owner_access_key": USER_AK,
    },
    "B: Admin with owner_access_key=user (expect 'not accessible' error)",
)

print(f"\n{'=' * 60}\nSUMMARY")
print(f"  A (admin self):     {'PASS' if resp_a.status_code < 400 else 'FAIL'} ({resp_a.status_code})")
print(f"  B (delegated):      {'PASS' if resp_b.status_code < 400 else 'FAIL'} ({resp_b.status_code})")
