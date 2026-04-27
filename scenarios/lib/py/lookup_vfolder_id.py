"""Print vfolder id whose name == $NAME, skipping deleted-state rows.

Used for my-search, admin-search, and project-search responses (all share
shape `items[].metadata.name | items[].name` and `items[].status`).
Reads search JSON from stdin.
"""
import json
import os
import sys

DELETED = {
    "delete-pending",
    "delete-ongoing",
    "delete-complete",
    "delete-error",
    "delete-aborted",
}
target = os.environ["NAME"]
for it in json.load(sys.stdin).get("items", []):
    name = (it.get("metadata") or {}).get("name") or it.get("name") or ""
    if name == target and it.get("status") not in DELETED:
        print(it["id"])
        break
