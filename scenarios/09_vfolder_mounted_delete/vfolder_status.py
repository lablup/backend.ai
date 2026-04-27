"""Print status of vfolder $VID in my-search response (or 'NOT_FOUND'). Reads JSON from stdin."""
import json
import os
import sys

vid = os.environ["VID"]
for it in json.load(sys.stdin).get("items", []):
    if it.get("id") == vid:
        print(it.get("status") or "UNKNOWN")
        sys.exit(0)
print("NOT_FOUND")
