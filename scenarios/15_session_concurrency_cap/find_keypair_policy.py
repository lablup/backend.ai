"""Print resource_policy of keypair whose access_key == $AK (defaults to 'default').

Reads admin keypair search JSON from stdin.
"""
import json
import os
import sys

ak = os.environ["AK"]
for it in json.load(sys.stdin).get("items", []):
    if it.get("access_key") == ak:
        print(it.get("resource_policy") or "default")
        break
