"""Print leaked vfolders (name starts with $PREFIX, status not in deleted set).

Prints lines of the form `<id> <name>`. Reads my-search JSON from stdin.
"""
import json
import os
import sys

prefix = os.environ["PREFIX"]
DELETED = {
    "delete-pending",
    "delete-ongoing",
    "delete-complete",
    "delete-error",
    "delete-aborted",
}
left = []
for it in json.load(sys.stdin).get("items", []):
    name = (it.get("metadata") or {}).get("name") or it.get("name", "")
    if name.startswith(prefix) and it.get("status") not in DELETED:
        left.append(f"{it['id']} {name}")
print("\n".join(left))
