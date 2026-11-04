from __future__ import annotations

from pathlib import Path

_OWNER_ONLY_DIR_MODE = 0o700
_OWNER_ONLY_FILE_MODE = 0o600


def make_missing_dirs_owner_only(directory: Path) -> None:
    if directory.is_dir():
        return
    # ``mkdir(parents=True)`` ignores ``mode`` for the parents it creates.
    make_missing_dirs_owner_only(directory.parent)
    directory.mkdir(mode=_OWNER_ONLY_DIR_MODE, exist_ok=True)


def ensure_owner_only_file(file_path: Path) -> None:
    make_missing_dirs_owner_only(file_path.parent)
    # ``touch(mode=...)`` only applies when it creates the file.
    file_path.touch(mode=_OWNER_ONLY_FILE_MODE)
    file_path.chmod(_OWNER_ONLY_FILE_MODE)
