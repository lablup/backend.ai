import asyncio
import os
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


async def _run(*argv: str) -> str:
    process = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await process.communicate()
    if process.returncode != 0:
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
            with open(backing, "wb") as image:
                os.truncate(image.fileno(), size)
            os.chmod(backing, 0o600)
            loop = await _run("losetup", "--find", "--show", "--nooverlap", str(backing))
            volumes.append(BlockVolume(backing, Path(loop), guest_path))
        return volumes

    async def release(self, kernel_id: KernelId) -> None:
        for guest_path in self._sizes:
            backing = self._backing(kernel_id, guest_path)
            if not backing.exists():
                continue
            attached = await _run("losetup", "--noheadings", "--output", "NAME", "--associated",
                                  str(backing))
            for loop in attached.split():
                await _run("losetup", "--detach", loop)
            backing.unlink(missing_ok=True)
