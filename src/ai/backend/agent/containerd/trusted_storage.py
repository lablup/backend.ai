"""Host-side trusted storage of a kernel: a sparse file attached as a loop block device."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from ai.backend.agent.errors.containerd import TrustedStorageUnavailable
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


def _allocate(backing: Path, size: int) -> None:
    fd = os.open(backing, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        os.ftruncate(fd, size)
    finally:
        os.close(fd)


async def _losetup(*args: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "losetup", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise TrustedStorageUnavailable(f"losetup {args[0]}: {err.decode().strip()}")
    return out.decode().strip()


async def _attached_to(backing: Path) -> list[str]:
    out = await _losetup("--noheadings", "--output", "NAME", "--associated", str(backing))
    return out.split()


async def attach_trusted_storage(backing: Path, size: int) -> Path:
    """Create the sparse file and return the loop device attached to it; repeatable."""
    try:
        await asyncio.to_thread(_allocate, backing, size)
        attached = await _attached_to(backing)
        if attached:
            return Path(attached[0])
        return Path(await _losetup("--find", "--show", "--nooverlap", str(backing)))
    except OSError as e:
        backing.unlink(missing_ok=True)
        raise TrustedStorageUnavailable(f"{backing}: {e}") from e
    except TrustedStorageUnavailable:
        backing.unlink(missing_ok=True)
        raise


async def detach_trusted_storage(backing: Path) -> None:
    """Detach the loop devices of the file and delete it; failures are logged, not raised."""
    try:
        if not backing.exists():
            return
        for loop in await _attached_to(backing):
            await _losetup("--detach", loop)
        backing.unlink(missing_ok=True)
    except (OSError, TrustedStorageUnavailable):
        log.warning("trusted storage release failed", backing=str(backing), exc_info=True)
