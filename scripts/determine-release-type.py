"""Classify a release version into the two values the release jobs branch on.

Prints them as ``KEY=value`` lines for a job output:

    python scripts/determine-release-type.py "$(cat VERSION)" >> "$GITHUB_OUTPUT"

======================= ==================== ================
Version suffix          ``RELEASE_AUDIENCE`` ``IS_PRERELEASE``
======================= ==================== ================
``aN``                  ``internal``         ``true``
``rcN``                 ``public``           ``true``
none, or ``.postN``     ``public``           ``false``
anything else           exit code 1
======================= ==================== ================
"""

import re
import sys

ALPHA = re.compile(r"a\d+$")
RELEASE_CANDIDATE = re.compile(r"rc\d+$")
FINAL = re.compile(r"\d+(\.\d+)*(\.post\d+)?$")


def classify(version: str) -> tuple[str, str]:
    if ALPHA.search(version):
        return "internal", "true"
    if RELEASE_CANDIDATE.search(version):
        return "public", "true"
    if FINAL.fullmatch(version):
        return "public", "false"
    raise ValueError(
        f"cannot classify the release grade of {version!r}: "
        "only an alpha (aN), a release candidate (rcN) and a final release are released"
    )


def main() -> None:
    try:
        audience, is_prerelease = classify(sys.argv[1].strip())
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"RELEASE_AUDIENCE={audience}")
    print(f"IS_PRERELEASE={is_prerelease}")


if __name__ == "__main__":
    main()
