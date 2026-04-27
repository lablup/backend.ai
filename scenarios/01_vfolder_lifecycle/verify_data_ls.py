"""Assert that 'inputs' and 'outputs' appear in a `bai vfolder ls` response. Reads JSON from stdin."""
import json
import sys

d = json.load(sys.stdin)
items = d.get("items") or d.get("files") or []
names = [it.get("name", it.get("path", "")) for it in items] if isinstance(items, list) else []
assert any("inputs" in (n or "") for n in names), f"inputs/ not found in {names}"
assert any("outputs" in (n or "") for n in names), f"outputs/ not found in {names}"
