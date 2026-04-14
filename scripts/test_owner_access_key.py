"""
Reproduce BA-5608: session creation with owner_access_key.

Test 1: Normal session creation (no owner_access_key) - should succeed
Test 2: Session creation with owner_access_key - should succeed but may fail due to bug
"""

import hashlib
import hmac
import json
import sys
from datetime import datetime, timezone

import requests

ENDPOINT = "http://127.0.0.1:8091"
API_VERSION = "v9.20250722"

ADMIN_AK = "AKIAIOSFODNN7EXAMPLE"
ADMIN_SK = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

USER_AK = "AKIANABBDUSEREXAMPLE"


def sign_request(method, uri, date, host, body_text, access_key, secret_key):
    sign_key = hmac.new(
        secret_key.encode("utf-8"), date.encode("utf-8"), hashlib.sha256
    ).digest()
    sign_str = (
        f"{method}\n{uri}\n{date}\n"
        f"host:{host}\n"
        f"content-type:application/json\n"
        f"x-backendai-version:{API_VERSION}\n"
        f"{body_text}"
    )
    signature = hmac.new(sign_key, sign_str.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"BackendAI signMethod=HMAC-SHA256, credential={access_key}:{signature}"


def create_session(access_key, secret_key, body_dict, label):
    now = datetime.now(timezone.utc)
    raw_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_key = now.strftime("%Y%m%d")
    body_text = json.dumps(body_dict)
    # Server uses empty body for hash in API version >= v4.20181215
    body_hash = hashlib.sha256(b"").hexdigest()
    uri = "/session"
    host = "127.0.0.1:8091"

    # sign_key = HMAC(HMAC(secret, YYYYMMDD), host)
    sign_key = hmac.new(
        secret_key.encode("utf-8"), date_key.encode("utf-8"), hashlib.sha256
    ).digest()
    sign_key = hmac.new(sign_key, host.encode("utf-8"), hashlib.sha256).digest()
    sign_str = (
        f"POST\n{uri}\n{raw_date}\n"
        f"host:{host}\n"
        f"content-type:application/json\n"
        f"x-backendai-version:{API_VERSION}\n"
        f"{body_hash}"
    )
    signature = hmac.new(sign_key, sign_str.encode("utf-8"), hashlib.sha256).hexdigest()
    auth = f"BackendAI signMethod=HMAC-SHA256, credential={access_key}:{signature}"
    headers = {
        "Content-Type": "application/json",
        "X-BackendAI-Version": API_VERSION,
        "X-BackendAI-Date": raw_date,
        "Authorization": auth,
    }

    print(f"\n{'='*60}")
    print(f"[{label}]")
    print(f"Access Key: {access_key}")
    if "owner_access_key" in body_dict:
        print(f"Owner Access Key: {body_dict['owner_access_key']}")

    resp = requests.post(f"{ENDPOINT}{uri}", headers=headers, data=body_text)
    print(f"Status: {resp.status_code}")
    try:
        result = resp.json()
        if resp.status_code >= 400:
            print(f"Error: {result.get('msg', result.get('title', 'unknown'))}")
        else:
            print(f"Result: sessionId={result.get('sessionId', '?')}, status={result.get('status', '?')}")
    except Exception:
        print(f"Response: {resp.text[:500]}")
    return resp


# Test 1: Admin creates own session (should work)
print("\n" + "=" * 60)
print("TEST 1: Admin creates own session (no owner_access_key)")
print("Expected: SUCCESS")
resp1 = create_session(
    ADMIN_AK,
    ADMIN_SK,
    {
        "clientSessionToken": "test-owner-" + datetime.now(timezone.utc).strftime("%H%M%S"),
        "image": "cr.backend.ai/stable/python:3.9-ubuntu22.04-amd64",
        "domain": "default",
        "group_name": "default",
        "enqueueOnly": True,
        "config": {
            "resources": {"cpu": 1, "mem": "512m"},
            "scaling_group": "default",
        },
    },
    "Admin's own session",
)

# Test 2: Admin creates session on behalf of user (the bug)
print("\n" + "=" * 60)
print("TEST 2: Admin creates session with owner_access_key=USER")
print("Expected: SUCCESS (but fails with bug)")
resp2 = create_session(
    ADMIN_AK,
    ADMIN_SK,
    {
        "clientSessionToken": "test-delegated-" + datetime.now(timezone.utc).strftime("%H%M%S"),
        "image": "cr.backend.ai/stable/python:3.9-ubuntu22.04-amd64",
        "domain": "default",
        "group_name": "default",
        "enqueueOnly": True,
        "owner_access_key": USER_AK,
        "config": {
            "resources": {"cpu": 1, "mem": "512m"},
            "scaling_group": "default",
        },
    },
    "Session on behalf of user",
)

# Summary
print("\n" + "=" * 60)
print("SUMMARY:")
print(f"  Test 1 (own session):   {'PASS' if resp1.status_code < 400 else 'FAIL'} ({resp1.status_code})")
print(f"  Test 2 (owner_access_key): {'PASS' if resp2.status_code < 400 else 'FAIL'} ({resp2.status_code})")

# Cleanup: terminate created sessions
for resp in [resp1, resp2]:
    if resp.status_code < 400:
        try:
            session_id = resp.json().get("sessionId")
            if session_id:
                date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                uri = f"/session/{session_id}"
                body = "{}"
                body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
                sign_key = hmac.new(ADMIN_SK.encode("utf-8"), date.encode("utf-8"), hashlib.sha256).digest()
                sign_str = f"DELETE\n{uri}\n{date}\nhost:127.0.0.1:8091\ncontent-type:application/json\nx-backendai-version:{API_VERSION}\n{body_hash}"
                sig = hmac.new(sign_key, sign_str.encode("utf-8"), hashlib.sha256).hexdigest()
                auth = f"BackendAI signMethod=HMAC-SHA256, credential={ADMIN_AK}:{sig}"
                headers = {
                    "Content-Type": "application/json",
                    "X-BackendAI-Version": API_VERSION,
                    "X-BackendAI-Date": raw_date,
                    "Authorization": auth,
                }
                requests.delete(f"{ENDPOINT}{uri}", headers=headers, data=body)
                print(f"  Cleaned up session: {session_id}")
        except Exception:
            pass
