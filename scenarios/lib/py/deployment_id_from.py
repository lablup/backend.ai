"""Print deployment id from a `deployment create` / `model-card deploy` response (stdin)."""
import json
import sys

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
print(
    d.get("id")
    or d.get("deployment_id")
    or d.get("deployment", {}).get("id")
    or ""
)
