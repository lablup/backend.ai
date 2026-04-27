"""Print ids of non-deleted vfolders whose name starts with $PREFIX. Reads my-search JSON from stdin."""
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
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for it in d.get("items", []):
    name = (it.get("metadata") or {}).get("name") or it.get("name") or ""
    if name.startswith(prefix) and it.get("status") not in DELETED:
        print(it["id"])
