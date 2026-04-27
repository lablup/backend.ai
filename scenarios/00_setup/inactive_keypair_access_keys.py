"""Print access_keys of inactive keypairs whose user_id == $TARGET_UID. Reads admin keypair search JSON from stdin."""
import json
import os
import sys

target = os.environ["TARGET_UID"]
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for it in d.get("items", []):
    if it.get("user_id") == target and not it.get("is_active"):
        print(it["access_key"])
