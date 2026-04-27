"""Print access_key of the first active keypair whose user_id == $TARGET_UID.

Reads admin keypair search JSON from stdin.
"""
import json
import os
import sys

target = os.environ["TARGET_UID"]
for it in json.load(sys.stdin).get("items", []):
    if it.get("user_id") == target and it.get("is_active"):
        print(it["access_key"])
        break
