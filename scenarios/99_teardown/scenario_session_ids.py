"""Print ids of non-terminal sessions whose name starts with $PREFIX. Reads my-search JSON from stdin."""
import json
import os
import sys

prefix = os.environ["PREFIX"]
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for it in d.get("items", []):
    name = (it.get("metadata") or {}).get("name") or it.get("name") or ""
    status = (it.get("lifecycle") or {}).get("status") or it.get("status") or ""
    if name.startswith(prefix) and status not in ("TERMINATED", "CANCELLED"):
        print(it["id"])
