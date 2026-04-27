"""Assert vfolder $EXPECT is in project-search items, $FORBID is not.

Reads project-search JSON from stdin. Exits non-zero with AssertionError on mismatch.
"""
import json
import os
import sys

ids = {it["id"] for it in json.load(sys.stdin).get("items", [])}
expect = os.environ["EXPECT"]
forbid = os.environ["FORBID"]
assert expect in ids, f"{expect} missing from listing"
assert forbid not in ids, f"{forbid} unexpectedly in listing"
