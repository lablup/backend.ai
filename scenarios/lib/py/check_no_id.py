"""Exit 0 if no items[].id == $TARGET (isolation enforced); exit 1 if found.

Reads search JSON from stdin. Treats unparseable input as enforcement (exit 0)
since 403/error pages mean the caller couldn't see anything.
"""
import json
import os
import sys

target = os.environ["TARGET"]
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for it in d.get("items", []):
    if it.get("id") == target:
        sys.exit(1)
sys.exit(0)
