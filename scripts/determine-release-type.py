"""Say whether a release version is a pre-release.

Prints ``true`` or ``false``. Turning that into a CI variable is the caller's
business:

    answer=$(python scripts/determine-release-type.py "$(cat VERSION)")
    echo "IS_PRERELEASE=$answer" >> "$GITHUB_ENV"
"""

import re
import sys


def main():
    version = sys.argv[1].strip()
    m = re.search(r"(rc\d+|a\d+|b\d+|dev\d+)$", version)
    print("true" if m is not None else "false")


if __name__ == "__main__":
    main()
