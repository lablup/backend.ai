"""Print count of sessions whose status is not in TERMINATED/CANCELLED/ERROR.

Reads my-search JSON from stdin.
"""
import json
import sys

TERM = {"TERMINATED", "CANCELLED", "ERROR"}
n = 0
for it in json.load(sys.stdin).get("items", []):
    s = (it.get("lifecycle") or {}).get("status") or it.get("status", "")
    if s and s not in TERM:
        n += 1
print(n)
