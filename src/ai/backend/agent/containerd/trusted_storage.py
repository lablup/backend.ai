"""Host-side trusted storage of a kernel: a sparse file attached as a loop block device."""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial
from pathlib import Path
from typing import Final

from ai.backend.agent.containerd.scratch import ScratchDirs, remove_scratch
from ai.backend.agent.errors.containerd import TrustedStorageUnavailable
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_LOSETUP: Final = "/sbin/losetup"


def _allocate(backing: Path, size: int) -> None:
    fd = os.open(backing, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        os.ftruncate(fd, size)
    finally:
        os.close(fd)


async def _losetup(*args: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        _LOSETUP, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise TrustedStorageUnavailable(f"losetup {args[0]}: {err.decode().strip()}")
    return out.decode().strip()


async def _attached_to(backing: Path) -> list[str]:
    out = await _losetup("--noheadings", "--output", "NAME", "--associated", str(backing))
    return out.split()


async def attach_trusted_storage(backing: Path, size: int) -> Path:
    """Create the sparse file and return the loop device attached to it."""
    try:
        await run_in_executor_with_context(None, partial(_allocate, backing, size))
        return Path(await _losetup("--find", "--show", "--nooverlap", str(backing)))
    except OSError as e:
        backing.unlink(missing_ok=True)
        raise TrustedStorageUnavailable(f"{backing}: {e}") from e
    except TrustedStorageUnavailable:
        backing.unlink(missing_ok=True)
        raise


async def detach_trusted_storage(backing: Path) -> bool:
    """Detach the loop devices of the file; False, with a warning, if one stays attached."""
    try:
        if backing.exists():
            for loop in await _attached_to(backing):
                await _losetup("--detach", loop)
    except (OSError, TrustedStorageUnavailable):
        log.warning("trusted storage detach failed", backing=str(backing), exc_info=True)
        return False
    return True


async def release_scratch(scratch_root: Path, kernel_id: str) -> None:
    """Detach the trusted storage, then remove the scratch holding its file; keep both on failure.

    Every scratch removal of a kernel that may hold trusted storage goes through here.
    """
    dirs = ScratchDirs.for_kernel(scratch_root, kernel_id)
    if not await detach_trusted_storage(dirs.trusted_store):
        log.warning("scratch kept, its trusted storage is still attached", kernel_id=kernel_id)
        return
    await run_in_executor_with_context(None, remove_scratch, scratch_root, kernel_id)
