"""Print session id from a `bai session enqueue` response (stdin)."""
import json
import sys

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
sid = (d.get("session") or {}).get("id") or d.get("id") or d.get("session_id")
if sid:
    print(sid)
