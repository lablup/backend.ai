"""Print lifecycle.status (or 'NOT_FOUND') of session whose id == $SID. Reads search JSON from stdin."""
import json
import os
import sys

sid = os.environ["SID"]
try:
    d = json.load(sys.stdin)
except Exception:
    print("NOT_FOUND")
    sys.exit(0)
for it in d.get("items", []):
    if it.get("id") == sid:
        status = (it.get("lifecycle") or {}).get("status") or it.get("status", "UNKNOWN")
        print(status)
        sys.exit(0)
print("NOT_FOUND")
