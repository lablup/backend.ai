"""Print the value of top-level JSON field named $FIELD. Reads JSON from stdin."""
import json
import os
import sys

print(json.load(sys.stdin)[os.environ["FIELD"]])
