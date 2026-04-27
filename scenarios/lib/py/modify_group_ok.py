"""Exit 0 if the modify_group GraphQL mutation returned ok=true. Reads response JSON from stdin."""
import json
import sys

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
ok = (d.get("data", {}).get("modify_group") or d.get("modify_group") or {}).get("ok")
sys.exit(0 if ok else 1)
