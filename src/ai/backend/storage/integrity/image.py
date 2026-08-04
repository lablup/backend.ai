from __future__ import annotations

import os
from pathlib import Path
from typing import Final

IMAGE_NAME: Final = ".bai-integrity.img"
SECTOR_SIZE: Final = 4096
TAG_SIZE: Final = 32
JOURNAL_FLOOR: Final = 64 * 1024 * 1024
JOURNAL_CEILING: Final = 1024 * 1024 * 1024
ALIGNMENT: Final = 1024 * 1024


class IntegrityImageRefusal(Exception):
    pass


def image_path(folder: Path) -> Path:
    return folder / IMAGE_NAME


def is_integrity_folder(folder: Path) -> bool:
    return image_path(folder).is_file()


def backing_size(capacity: int) -> int:
    tags = -(-capacity // SECTOR_SIZE) * TAG_SIZE
    journal = min(max(capacity // 16, JOURNAL_FLOOR), JOURNAL_CEILING)
    total = capacity + tags + journal + ALIGNMENT
    return -(-total // ALIGNMENT) * ALIGNMENT


def footprint(folder: Path) -> int:
    path = image_path(folder)
    return path.stat().st_blocks * 512 if path.is_file() else 0


def provision(folder: Path, capacity: int) -> Path:
    if capacity <= 0:
        raise IntegrityImageRefusal("an integrity-tier folder needs a positive declared capacity")
    folder.mkdir(parents=True, exist_ok=True)
    path = image_path(folder)
    try:
        handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise IntegrityImageRefusal(f"{folder} already carries an integrity-tier image")
    try:
        os.ftruncate(handle, backing_size(capacity))
    finally:
        os.close(handle)
    return path


def grow(folder: Path, capacity: int) -> int:
    path = image_path(folder)
    if not path.is_file():
        raise IntegrityImageRefusal(f"{folder} carries no integrity-tier image")
    current = path.stat().st_size
    wanted = backing_size(capacity)
    if wanted < current:
        raise IntegrityImageRefusal(
            f"{folder} holds an integrity-tier image that cannot shrink from {current} to {wanted}"
        )
    os.truncate(path, wanted)
    return wanted


def destroy(folder: Path) -> None:
    image_path(folder).unlink(missing_ok=True)
