import json
import subprocess
import sys
import re


def pad_zero(num: int, size: int) -> str:
    return "".join([*(["0"] * min(size - len(str(num)), 0)), str(num)])


rc_regex = re.compile(r"(\d+)rc(\d+)")
dev_regex = re.compile(r"(\d+)dev(\d+)")

release_id = sys.argv[1]
major, minor, patch = release_id.split(".", maxsplit=3)

if (rc_patch_ver := rc_regex.findall(patch)):
    patch_ver, rc_ver = rc_patch_ver[0]
    if rc_ver == "1":
        prev_patch = str(int(patch_ver)-1)
    else:
        prev_patch = f"{patch_ver}rc{int(rc_ver)-1}"
elif (dev_patch_ver := dev_regex.findall(patch)):
    patch_ver, dev_ver = dev_patch_ver[0]
    prev_patch = f"{patch_ver}dev{int(dev_ver)-1}"
else:
    prev_patch = pad_zero(int(patch)-1, 2)

prev_release = f"{major}.{minor}.{prev_patch}"

backports_since = subprocess.check_output(["git", "log", f"{prev_release}..{major}.{minor}", "--oneline"]).decode("utf-8")
release_date = subprocess.check_output(["git", "log", f"{prev_release}~1..{prev_release}", "--pretty=format:'%ad'", "--date=format:'%Y-%m-%d'"]).decode("utf-8").replace("''", "")
merges_since_json = subprocess.check_output(["gh", "pr", "list", "--search", f"merged:>={release_date} milestone:{major}.{minor}", "-s", "merged", "--json", "number,mergeCommit"]).decode("utf-8")
merges_since = json.loads(merges_since_json)

failed_commits = 0
for pr_info in merges_since:
    pr_number = pr_info["number"]
    commit_sha = pr_info["mergeCommit"]["oid"]
    if f"#{pr_number}" not in backports_since:
        print(f"Could not find PR #{pr_number} (https://github.com/lablup/backend.ai/pull/{pr_number}, main commit SHA {commit_sha}) from backport list")
        failed_commits += 1
    else:
        print(f"Found PR #{pr_number} from backport list")

if failed_commits > 0:
    print(f"Among the {len(merges_since)} merged PRs we found {failed_commits} are not yet backported")
else:
    print(f"Looks like all {len(merges_since)} are backported")

sys.exit(0 if failed_commits == 0 else 1)
