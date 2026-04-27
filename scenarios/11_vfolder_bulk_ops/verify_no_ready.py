"""Exit 1 if any id in $TARGETS (comma-separated) appears with status 'ready' in my-search.

Reads my-search JSON from stdin.
"""
import json
import os
import sys

targets = set(os.environ["TARGETS"].split(","))
ready_leak = [
    it["id"]
    for it in json.load(sys.stdin).get("items", [])
    if it.get("id") in targets and it.get("status") == "ready"
]
if ready_leak:
    print("READY_AFTER_PURGE", ",".join(ready_leak))
    sys.exit(1)
sys.exit(0)
