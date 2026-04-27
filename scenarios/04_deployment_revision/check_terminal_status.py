"""Verify deployment $TARGET in project-search response is in a terminal state.

Exit 0 if status ∈ {STOPPED, DESTROYED, DELETED, TERMINATED, CANCELLED}, or if
the row is absent (also acceptable). Exit 1 otherwise. Reads search JSON from stdin.
"""
import json
import os
import sys

target = os.environ["TARGET"]
TERM = {"STOPPED", "DESTROYED", "DELETED", "TERMINATED", "CANCELLED"}
for it in json.load(sys.stdin).get("items", []):
    if it.get("id") == target:
        st = (it.get("lifecycle") or {}).get("status") or it.get("status") or ""
        if st in TERM:
            print(f"terminal: {st}")
            sys.exit(0)
        print(f"NOT TERMINAL: {st}")
        sys.exit(1)
print("absent (also acceptable)")
sys.exit(0)
