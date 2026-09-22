"""Check `determine-release-type.py`. Run it directly: `python scripts/test_determine_release_type.py`.

`/scripts/` is outside the pants source tree, so this cannot be a pants test.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("determine-release-type.py")

CLASSIFIED = [
    ("26.9.0a4", "internal", "true"),
    ("26.9.0rc1", "public", "true"),
    ("26.9.0", "public", "false"),
    ("26.9.1.post1", "public", "false"),
]
REJECTED = ["26.9.0b1", "26.9.0dev1", "26.9.0rc", "26.9.0-alpha", ""]


def run(version: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), version], capture_output=True, text=True
    )


def main() -> None:
    for version, audience, is_prerelease in CLASSIFIED:
        result = run(version)
        assert result.returncode == 0, f"{version}: exited {result.returncode}"
        expected = f"RELEASE_AUDIENCE={audience}\nIS_PRERELEASE={is_prerelease}\n"
        assert result.stdout == expected, f"{version}: got {result.stdout!r}"

    for version in REJECTED:
        result = run(version)
        assert result.returncode == 1, f"{version}: exited {result.returncode}"
        assert result.stdout == "", f"{version}: got {result.stdout!r}"

    print(f"OK: {len(CLASSIFIED) + len(REJECTED)} versions")


if __name__ == "__main__":
    main()
