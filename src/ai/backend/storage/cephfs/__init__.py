import asyncio
import os
import shutil
from typing import Dict, FrozenSet, List
from uuid import UUID

from ai.backend.common.types import BinarySize
from ai.backend.storage.abc import CAP_QUOTA, CAP_VFOLDER

from ..exception import ExecutionError
from ..types import FSUsage, Optional, VFolderCreationOptions
from ..vfs import BaseVolume


async def run(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if err:
        raise ExecutionError(err.decode())
    return out.decode()


class CephFSVolume(BaseVolume):
    loop: asyncio.AbstractEventLoop
    registry: Dict[str, int]
    project_id_pool: List[int]

    async def init(self) -> None:
        available = True
        try:
            await asyncio.create_subprocess_exec(
                b"ceph",
                b"--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            available = False

        if not available:
            raise RuntimeError("Ceph is not installed. ")

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA])

    # ----- volume operations -----
    async def create_vfolder(
        self,
        vfid: UUID,
        options: Optional[VFolderCreationOptions] = None,
        *,
        exist_ok: bool = False
    ) -> None:
        vfpath = self.mangle_vfpath(vfid)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: vfpath.mkdir(0o755, parents=True, exist_ok=exist_ok),
        )
        if not (options is None or options.quota is None or options.quota == 0):
            quota = options.quota
            await self.set_quota(vfpath, quota)

    async def get_fs_usage(self) -> FSUsage:
        (total, used, _) = await asyncio.get_running_loop().run_in_executor(
            None,
            shutil.disk_usage,
            self.mount_path,
        )
        return FSUsage(
            capacity_bytes=BinarySize(total),
            used_bytes=BinarySize(used),
        )

    async def get_quota(self, vfpath) -> BinarySize:
        loop = asyncio.get_running_loop()
        raw_report = await loop.run_in_executor(
            None,
            # without type: ignore mypy will raise error when trying to run on macOS
            # because os.getxattr() is only for linux
            lambda: os.getxattr(vfpath, "ceph.quota.max_bytes"),  # type: ignore[attr-defined]
        )
        report = str(raw_report)
        if len(report.split()) != 6:
            raise ExecutionError("ceph quota report output is in unexpected format")
        _, quota = report.split("=")
        quota = quota.replace('"', "")
        return BinarySize(quota)

    async def set_quota(self, vfpath, size_bytes: BinarySize) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            # without type: ignore mypy will raise error when trying to run on macOS
            # because os.setxattr() is only for linux
            lambda: os.setxattr(vfpath, "ceph.quota.max_bytes", str(int(size_bytes)).encode()),  # type: ignore[attr-defined]
        )
