"""Host-side trusted storage of a kernel: a sparse file attached as a loop block device."""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial
from pathlib import Path
from typing import Final

from ai.backend.agent.containerd.sealed import remove_spec_dir
from ai.backend.agent.errors.containerd import TrustedStorageUnavailable
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

TRUSTED_STORE_NAME: Final = "trusted-store.img"
_LOSETUP: Final = "/sbin/losetup"
_LOSETUP_TIMEOUT_SEC: Final = 30.0


def trusted_store_path(scratch_root: Path, kernel_id: str) -> Path:
    return scratch_root / kernel_id / TRUSTED_STORE_NAME


def _allocate(backing: Path, size: int) -> None:
    backing.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(backing, flags, 0o600)
    try:
        os.ftruncate(fd, size)
    finally:
        os.close(fd)


async def _losetup(*args: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        _LOSETUP, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        async with asyncio.timeout(_LOSETUP_TIMEOUT_SEC):
            out, err = await proc.communicate()
    except BaseException as e:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
        if isinstance(e, TimeoutError):
            raise TrustedStorageUnavailable(f"losetup {args[0]}: timed out") from e
        raise
    if proc.returncode != 0:
        raise TrustedStorageUnavailable(
            f"losetup {args[0]} exited with {proc.returncode}: {err.decode(errors='replace').strip()}"
        )
    return out.decode(errors="replace").strip()


async def attach_trusted_storage(backing: Path, size: int) -> Path:
    """Create the sparse file and return the loop device attached to it."""
    try:
        await asyncio.to_thread(partial(_allocate, backing, size))
        device = await _losetup("--find", "--show", "--nooverlap", str(backing))
        if not device.startswith("/dev/loop"):
            raise TrustedStorageUnavailable(f"losetup returned an unexpected device: {device!r}")
        return Path(device)
    except OSError as e:
        await asyncio.to_thread(partial(backing.unlink, missing_ok=True))
        raise TrustedStorageUnavailable(f"{backing}: {e}") from e
    except TrustedStorageUnavailable:
        await asyncio.to_thread(partial(backing.unlink, missing_ok=True))
        raise


async def detach_trusted_storage(backing: Path) -> bool:
    """Detach the loop devices of the file; False, with a warning, if one stays attached."""
    try:
        # The file is removed only after its detach, so no file means nothing is attached.
        if await asyncio.to_thread(backing.exists):
            attached = await _losetup(
                "--noheadings", "--output", "NAME", "--associated", str(backing)
            )
            for loop in attached.split():
                await _losetup("--detach", loop)
    except (OSError, TrustedStorageUnavailable):
        log.warning("trusted storage detach failed", backing=str(backing), exc_info=True)
        return False
    return True


async def release_scratch(scratch_root: Path, kernel_id: str) -> None:
    """Detach the trusted storage, then remove the kernel's scratch dir; keep both on failure."""
    if not await detach_trusted_storage(trusted_store_path(scratch_root, kernel_id)):
        log.warning("scratch kept, its trusted storage is attached", kernel_id=kernel_id)
        return
    await asyncio.to_thread(remove_spec_dir, scratch_root, kernel_id)
