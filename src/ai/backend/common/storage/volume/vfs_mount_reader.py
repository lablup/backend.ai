"""Reads what identifies a vfs mount, run as a child process's ``-c`` source.

It imports nothing but the standard library: the child does not share the parent's ``sys.path``.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class MountSnapshot:
    device_id: int
    marker_file_content: str | None


def read_mount(mount_path: Path, marker_path: Path) -> MountSnapshot:
    """Blocks in the kernel while it reads: a dead network mount hangs in ``statvfs``."""
    os.statvfs(mount_path)
    try:
        marker_file_content: str | None = marker_path.read_text().strip() or None
    except FileNotFoundError:
        marker_file_content = None
    return MountSnapshot(
        device_id=mount_path.stat().st_dev,
        marker_file_content=marker_file_content,
    )


def main() -> None:
    try:
        snapshot = read_mount(Path(sys.argv[1]), Path(sys.argv[2]))
    except OSError as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(1)
    sys.stdout.write(json.dumps(asdict(snapshot)) + "\n")


if __name__ == "__main__":
    main()
