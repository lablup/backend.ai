"""Verify file $NAME exists in `bai vfolder ls` output with size $SIZE bytes.

Reads ls JSON from stdin. Exits 0 on match, 1 on size mismatch or missing.
"""
import json
import os
import sys

target = os.environ["NAME"]
expected = int(os.environ["SIZE"])
d = json.load(sys.stdin)
items = d.get("items") or d.get("files") or d
if isinstance(items, dict):
    items = items.get("items") or []
for it in items:
    if (it.get("name") or it.get("filename") or "") == target:
        size = it.get("size")
        if size is None or int(size) != expected:
            print(f"SIZE_MISMATCH expected={expected} got={size}")
            sys.exit(1)
        print("OK")
        sys.exit(0)
print("NOT_FOUND")
sys.exit(1)
