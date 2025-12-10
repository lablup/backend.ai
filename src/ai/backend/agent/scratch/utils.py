import asyncio
import os
import shutil
import subprocess
from collections.abc import Mapping
from functools import partial
from pathlib import Path
from typing import Optional

import aiofiles

from ai.backend.common.json import load_json
from ai.backend.common.types import KernelId

from ..resources import KernelResourceSpec
from .types import KernelRecoveryScratchData


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


class ScratchUtils:
    @staticmethod
    def get_scratch_kernel_config_dir(scratch_root: Path, kernel_id: KernelId) -> Path:
        return scratch_root / str(kernel_id) / "config"


class ScratchConfig:
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    def _json_recovery_file_path(self) -> Path:
        return self._config_path / "recovery.json"

    def _environ_file_path(self) -> Path:
        return self._config_path / "environ.txt"

    def _resource_file_path(self) -> Path:
        return self._config_path / "resource.txt"

    def recovery_file_exists(self) -> bool:
        return self._json_recovery_file_path().is_file()

    async def get_json_recovery_data(self) -> Optional[KernelRecoveryScratchData]:
        filepath = self._json_recovery_file_path()
        if not filepath.is_file():
            return None
        async with aiofiles.open(filepath, "r") as file:
            text = await file.read()
        raw_data = load_json(text)
        return KernelRecoveryScratchData.model_validate(raw_data)

    async def get_kernel_environ(self) -> Mapping[str, str]:
        result: dict[str, str] = {}
        filepath = self._environ_file_path()
        raw_data = filepath.read_text()
        for line in raw_data.splitlines():
            k, _, v = line.partition("=")
            result[k] = v
        return result

    async def get_kernel_resource_spec(self) -> KernelResourceSpec:
        filepath = self._resource_file_path()
        raw_data = filepath.read_text()
        return KernelResourceSpec.read_from_string(raw_data)

    async def save_json_recovery_data(self, data: KernelRecoveryScratchData) -> None:
        filepath = self._json_recovery_file_path()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        serialized = data.model_dump_json()
        async with aiofiles.open(filepath, "w") as file:
            await file.write(serialized)
