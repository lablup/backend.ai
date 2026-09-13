"""
Container entrypoint launcher: run /opt/kernel/entrypoint.sh with whichever POSIX shell the image has.

The agent starts every kernel container through this file using the kernel runner's own Python
under /opt/backend.ai, so images without /bin/sh (for example distroless bases that ship only
bash) still start. /bin/sh is tried first, so images that have it keep their current interpreter.
"""

import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import NoReturn

ENTRYPOINT_SCRIPT = "/opt/kernel/entrypoint.sh"
SHELL_CANDIDATES: tuple[str, ...] = (
    "/bin/sh",
    "/usr/bin/sh",
    "/bin/bash",
    "/usr/bin/bash",
    "/bin/ash",
    "/usr/bin/ash",
    "/bin/dash",
    "/usr/bin/dash",
)


def find_shell(candidates: Iterable[str] = SHELL_CANDIDATES) -> str | None:
    """Return the first candidate that is an executable regular file (symlinks followed)."""
    for path in candidates:
        if Path(path).is_file() and os.access(path, os.X_OK):
            return path
    return None


def main(argv: list[str]) -> NoReturn:
    shell = find_shell()
    if shell is None:
        print(
            "ERROR: the image has no POSIX shell to run the kernel entrypoint "
            f"(tried: {', '.join(SHELL_CANDIDATES)})",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(127)
    # The shell runs under its own name; when /bin/sh is a symlink to bash this is the same
    # POSIX mode as before, and the bash fallback runs the script in plain bash mode.
    try:
        os.execv(shell, [shell, ENTRYPOINT_SCRIPT, *argv])
    except OSError as e:
        print(
            f"ERROR: cannot execute {shell} to run the kernel entrypoint: {e.strerror}",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(126)


if __name__ == "__main__":
    main(sys.argv[1:])
