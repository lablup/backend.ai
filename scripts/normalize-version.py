"""Print the PEP 440-normalized form of a version string.

The normalized form is what the docker image tags use.  A version with a local
segment (e.g., ``26.9.0+dev``) is rejected because ``+`` is not a legal
character in a docker tag.  Turning the printed value into a CI variable is
the caller's business:

    PKGVER=$(python scripts/normalize-version.py "$(cat VERSION)")
    echo "version=$PKGVER" >> "$GITHUB_OUTPUT"
"""

import sys

from packaging.version import InvalidVersion, Version


def main() -> None:
    raw = sys.argv[1].strip()
    try:
        version = Version(raw)
    except InvalidVersion:
        print(f"error: {raw!r} is not a valid PEP 440 version", file=sys.stderr)
        sys.exit(1)
    if version.local is not None:
        print(
            f"error: {raw!r} has a local version segment"
            " ('+' is not a legal character in a docker tag)",
            file=sys.stderr,
        )
        sys.exit(1)
    print(version)


if __name__ == "__main__":
    main()
