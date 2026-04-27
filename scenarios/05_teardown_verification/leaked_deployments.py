"""Print leaked deployments (name starts with $PREFIX, status not in terminal set).

Prints lines of the form `<id> <name> [<status>]`. Reads my-search JSON from stdin.
"""
import json
import os
import sys

prefix = os.environ["PREFIX"]
TERMINAL = {"STOPPED", "DESTROYED", "DELETED", "TERMINATED", "CANCELLED"}
try:
    d = json.load(sys.stdin)
except Exception:
    print("")
    sys.exit(0)
left = []
for it in d.get("items", []):
    md = it.get("metadata") or {}
    name = md.get("name") or it.get("name", "")
    status = md.get("status") or it.get("status", "")
    if name.startswith(prefix) and status not in TERMINAL:
        left.append(f"{it['id']} {name} [{status}]")
print("\n".join(left))
