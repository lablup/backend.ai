"""Print user id whose email == $EMAIL. Reads search JSON from stdin."""
import json
import os
import sys

target = os.environ["EMAIL"]
for it in json.load(sys.stdin).get("items", []):
    info = it.get("basic_info") or {}
    if info.get("email") == target or it.get("email") == target:
        print(it["id"])
        break
