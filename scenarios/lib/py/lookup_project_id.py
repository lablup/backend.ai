"""Print project id whose basic_info.name == $NAME. Reads search JSON from stdin."""
import json
import os
import sys

target = os.environ["NAME"]
for it in json.load(sys.stdin).get("items", []):
    if it.get("basic_info", {}).get("name") == target:
        print(it["id"])
        break
