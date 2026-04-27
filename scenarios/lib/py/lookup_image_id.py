"""Print image id whose name == $NAME. Reads search JSON from stdin."""
import json
import os
import sys

target = os.environ["NAME"]
for it in json.load(sys.stdin).get("items", []):
    if it.get("name") == target:
        print(it["id"])
        break
