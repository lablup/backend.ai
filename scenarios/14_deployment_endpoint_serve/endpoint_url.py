"""Print deployment endpoint URL from a `deployment get` response, if populated.

Reads JSON from stdin. Prints nothing (and exits 0) if URL is absent or 'null'.
"""
import json
import sys

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
na = d.get("network_access") or d.get("networkAccess") or {}
url = na.get("endpoint_url") or d.get("endpoint_url") or ""
if url and url.lower() != "null":
    print(url)
