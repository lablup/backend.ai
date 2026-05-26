"""Filesystem helpers and constants for TUS chunk payload files."""

from __future__ import annotations

import errno
import secrets
from pathlib import Path

import aiofiles.os

CHUNKS_DIRNAME = "chunks"

_TEMP_SUFFIX_BYTES = 8


def committed_chunk_path(chunks_dir: Path, offset: int) -> Path:
    """Final on-disk path of the committed chunk for ``offset``."""
    return chunks_dir / f"chunk_{offset}.dat"


def temp_chunk_path(chunks_dir: Path, offset: int) -> Path:
    """Unique staging path for an in-flight chunk at ``offset``.

    The random suffix lets concurrent storage-proxy replicas write into the
    same offset without sharing a temp path.
    """
    return chunks_dir / f"chunk_{offset}.{_random_token()}.tmp"


def staging_path(target: Path) -> Path:
    """Unique sibling path of ``target`` for atomic-rename writes."""
    return target.with_name(f"{target.name}.{_random_token()}.tmp")


async def unlink_quietly(path: Path) -> None:
    """
    Best-effort delete used in rollback/cleanup paths where the file may have
    already been removed by a concurrent worker or never created.
    """
    try:
        await aiofiles.os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def _random_token() -> str:
    return secrets.token_hex(_TEMP_SUFFIX_BYTES)
