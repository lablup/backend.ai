"""Print id of the first item from `items` (or `presets`). Reads JSON from stdin."""
import json
import sys

d = json.load(sys.stdin)
items = d.get("items") or d.get("presets") or []
print(items[0]["id"] if items else "")
