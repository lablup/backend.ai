import asyncio
import os
import time
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.types import KernelId

from .errors import BlockVolumeUnavailable

SCRATCH_GUEST_PATH = Path("/dev/bai_scratch")
IMAGE_STORE_GUEST_PATH = Path("/dev/trusted_store")


@dataclass(frozen=True)
class BlockVolume:
    backing: Path
    loop: Path
    guest_path: Path


def _allocate(backing: Path, size: int) -> None:
    handle = os.open(backing, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.ftruncate(handle, size)
    finally:
        os.close(handle)
    backing.chmod(0o600)


async def _run(*argv: str, check: bool = True) -> str:
    process = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await process.communicate()
    if check and process.returncode != 0:
        raise BlockVolumeUnavailable(extra_msg=f"{argv[0]}: {err.decode().strip()}")
    return out.decode().strip()


class BlockVolumeManager:
    def __init__(self, root: Path, scratch_bytes: int, image_store_bytes: int) -> None:
        self._root = root
        self._sizes = {
            SCRATCH_GUEST_PATH: scratch_bytes,
            IMAGE_STORE_GUEST_PATH: image_store_bytes,
        }

    def _backing(self, kernel_id: KernelId, guest_path: Path) -> Path:
        return self._root / f"{kernel_id}{guest_path.name}.img"

    async def provision(self, kernel_id: KernelId) -> list[BlockVolume]:
        self._root.mkdir(mode=0o700, parents=True, exist_ok=True)
        volumes: list[BlockVolume] = []
        for guest_path, size in self._sizes.items():
            if size <= 0:
                continue
            backing = self._backing(kernel_id, guest_path)
            await asyncio.to_thread(_allocate, backing, size)
            loop = await _run("losetup", "--find", "--show", "--nooverlap", str(backing))
            volumes.append(BlockVolume(backing, Path(loop), guest_path))
        return volumes

    async def _release_backing(self, backing: Path) -> bool:
        if not backing.exists():
            return False
        attached = await _run(
            "losetup",
            "--noheadings",
            "--output",
            "NAME",
            "--associated",
            str(backing),
            check=False,
        )
        for loop in attached.split():
            await _run("losetup", "--detach", loop, check=False)
        backing.unlink(missing_ok=True)
        return True

    async def release(self, kernel_id: KernelId) -> None:
        for guest_path in self._sizes:
            await self._release_backing(self._backing(kernel_id, guest_path))

    async def reclaim(self, live: Collection[KernelId], grace: float = 900.0) -> list[str]:
        if not self._root.is_dir():
            return []
        owned = tuple(str(kernel_id) for kernel_id in live)
        cutoff = time.time() - grace
        dropped: list[str] = []
        for backing in sorted(self._root.glob("*.img")):
            if backing.name.startswith(owned) or backing.stat().st_mtime > cutoff:
                continue
            if await self._release_backing(backing):
                dropped.append(backing.name)
        return dropped
