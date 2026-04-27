"""Verify every id in $TARGETS (comma-separated) appears in my-search with a deleted-state status.

Reads my-search JSON from stdin. Prints diagnostics to stdout; exits 1 on any miss.
"""
import json
import os
import sys

targets = set(os.environ["TARGETS"].split(","))
DELETED = {
    "delete-pending",
    "delete-ongoing",
    "delete-complete",
    "delete-error",
    "delete-aborted",
}
seen = {it["id"]: it.get("status") for it in json.load(sys.stdin).get("items", []) if it.get("id") in targets}
missing = targets - set(seen.keys())
not_deleted = [vid for vid, s in seen.items() if s not in DELETED]
if missing:
    print("MISSING_FROM_LIST", ",".join(missing))
if not_deleted:
    print("NOT_IN_DELETED_STATE", ",".join(not_deleted))
sys.exit(0 if (not missing and not not_deleted) else 1)
