"""Print leaked sessions (name starts with $PREFIX, status not TERMINATED/CANCELLED).

Prints lines of the form `<id> <name> [<status>]`. Reads my-search JSON from stdin.
"""
import json
import os
import sys

prefix = os.environ["PREFIX"]
left = []
for it in json.load(sys.stdin).get("items", []):
    name = (it.get("metadata") or {}).get("name") or it.get("name") or ""
    status = (it.get("lifecycle") or {}).get("status") or it.get("status", "")
    if name.startswith(prefix) and status not in ("TERMINATED", "CANCELLED"):
        left.append(f"{it['id']} {name} [{status}]")
print("\n".join(left))
