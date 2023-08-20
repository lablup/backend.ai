import json
import subprocess
import sys


def pad_zero(num: int, size: int) -> str:
    return "".join([*(["0"] * min(size - len(str(num)), 0)), str(num)])


release_id = sys.argv[1]
major, minor, patch = release_id.split(".", maxsplit=3)
prev_release = f"{major}.{minor}.{pad_zero(int(patch)-1, 2)}"

backports_since = subprocess.check_output(["git", "log", f"{prev_release}..{major}.{minor}", "--oneline"]).decode("utf-8")
release_date = subprocess.check_output(["git", "log", f"{prev_release}~1..{prev_release}", "--pretty=format:'%ad'", "--date=format:'%Y-%m-%d'"]).decode("utf-8").replace("''", "")
merges_since = subprocess.check_output(["gh", "pr", "list", "--search", f"merged:>={release_date} milestone:{major}.{minor}", "-s", "merged", "--json", "number,mergeCommit"]).decode("utf-8")
for pr_info in json.loads(merges_since):
    pr_number = pr_info["number"]
    commit_sha = pr_info["mergeCommit"]["oid"]
    if f"#{pr_number}" not in backports_since:
        print(f"Could not find PR #{pr_number} (https://github.com/lablup/backend.ai/pull/{pr_number}, main commit SHA {commit_sha}) from backport list")
    else:
        print(f"Found PR #{pr_number} from backport list")
