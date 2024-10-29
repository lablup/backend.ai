import asyncio
import os
import shutil
import subprocess
from functools import partial
from pathlib import Path

from ai.backend.common.types import KernelId


def create_sparse_file(name: str, size: int) -> None:
    fd = os.open(name, os.O_CREAT, 0o644)
    os.close(fd)
    os.truncate(name, size)
    # Check that no space was allocated
    stat = os.stat(name)
    if stat.st_blocks != 0:
        raise RuntimeError("could not create sparse file")


async def create_loop_filesystem(
    scratch_root: Path, scratch_size: int, kernel_id: KernelId
) -> None:
    loop = asyncio.get_running_loop()
    scratch_dir = (scratch_root / f"{kernel_id}").resolve()
    scratch_file = (scratch_root / f"{kernel_id}.img").resolve()
    await loop.run_in_executor(None, partial(os.makedirs, str(scratch_dir), exist_ok=True))
    await loop.run_in_executor(None, create_sparse_file, str(scratch_file), scratch_size)
    mkfs = await asyncio.create_subprocess_exec(
        "/sbin/mkfs.ext4", str(scratch_file), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    exit_code = await mkfs.wait()
    if exit_code != 0:
        raise RuntimeError("mkfs failed")
    mount = await asyncio.create_subprocess_exec("mount", str(scratch_file), str(scratch_dir))
    exit_code = await mount.wait()
    if exit_code != 0:
        raise RuntimeError("mount failed")


async def destroy_loop_filesystem(scratch_root: Path, kernel_id: KernelId) -> None:
    loop = asyncio.get_running_loop()
    scratch_dir = (scratch_root / f"{kernel_id}").resolve()
    scratch_file = (scratch_root / f"{kernel_id}.img").resolve()
    umount = await asyncio.create_subprocess_exec("umount", str(scratch_dir))
    exit_code = await umount.wait()
    if exit_code != 0:
        raise RuntimeError("umount failed")
    await loop.run_in_executor(None, os.remove, str(scratch_file))
    await loop.run_in_executor(None, shutil.rmtree, str(scratch_dir))
