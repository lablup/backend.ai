#!/usr/bin/env python3
"""Test keypair/user resource policy queries across different roles."""
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

ACCOUNTS = {
    "superadmin": ("AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
    "domain-admin": ("AKIAHUKCHDEZGEXAMPLE", "cWbsM_vBB4CzTW7JdORRMx8SjGI3-wEXAMPLEKEY"),
    "user": ("AKIANABBDUSEREXAMPLE", "C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf"),
    "user2": ("AKIANATWOUSEREXAMPLE", "P7oxTDdzHbEpUSs5v7r7EWj9yKstp8VpZ7SEyA-g"),
    "monitor": ("AKIANAMONITOREXAMPLE", "7tuEwF1J7FfK41vOM4uSSyWCUWjPBolpVwvgkSBu"),
}


def send_gql(query, access_key, secret_key):
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
    r = requests.post(str(API_ENDPOINT / rel_url[1:]), headers=headers, json={"query": query})
    return r.json()


KRP_QUERY = textwrap.dedent("""
    query {
        keypair_resource_policies {
            name
            max_concurrent_sessions
        }
    }
""").strip()

URP_QUERY = textwrap.dedent("""
    query {
        user_resource_policies {
            name
            max_vfolder_count
        }
    }
""").strip()

for query_name, query in [("keypair_resource_policies", KRP_QUERY), ("user_resource_policies", URP_QUERY)]:
    print(f"\n{'=' * 70}")
    print(f"  {query_name}")
    print(f"{'=' * 70}")
    for role, (ak, sk) in ACCOUNTS.items():
        result = send_gql(query, ak, sk)
        data = result.get("data", {}).get(query_name)
        errors = result.get("errors")
        if errors:
            names = f"ERROR: {errors[0]['message']}"
            count = 0
        elif data:
            names = [p["name"] for p in data]
            count = len(data)
        else:
            names = "null"
            count = 0
        print(f"  {role:15s} → {count} items: {names}")
