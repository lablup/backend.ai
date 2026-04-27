"""Exit 0 if any items[].id == $TARGET, else exit 1. Reads search JSON from stdin."""
import json
import os
import sys

target = os.environ["TARGET"]
for it in json.load(sys.stdin).get("items", []):
    if it.get("id") == target:
        sys.exit(0)
sys.exit(1)
