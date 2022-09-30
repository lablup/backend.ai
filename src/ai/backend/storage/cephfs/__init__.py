import asyncio
from typing import Dict, List
from uuid import UUID

from ai.backend.common.types import BinarySize

from ..exception import ExecutionError
from ..types import FSUsage, VFolderCreationOptions
from ..vfs import BaseVolume


async def read_file(loop: asyncio.AbstractEventLoop, filename: str) -> str:
    def _read():
        with open(filename, "r") as fr:
            return fr.read()

    return await loop.run_in_executor(None, lambda: _read())


async def write_file(loop: asyncio.AbstractEventLoop, filename: str, contents: str, perm="w"):
    def _write():
        with open(filename, perm) as fw:
            fw.write(contents)

    await loop.run_in_executor(None, lambda: _write())


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

    # ----- volume opeartions -----
    async def create_vfolder(self, vfid: UUID, options: VFolderCreationOptions = None) -> None:
        vfpath = self.mangle_vfpath(vfid)
        await run(f"mkdir -p {vfpath}")
        if not (options is None or options.quota is None or options.quota == 0):
            quota = options.quota
            await self.set_quota(vfpath, quota)

    async def get_fs_usage(self) -> FSUsage:
        stat = await run(f"df -h {self.mount_path} | grep {self.mount_path}")
        _, capacity, used, _, _, path = stat.split()
        if len(stat.split()) == 6:
            raise ExecutionError("'df -h' stdout is in an unexpected format")
        if str(self.mount_path) != path:
            raise ExecutionError("'df -h' stdout is in an unexpected format")
        return FSUsage(
            capacity_bytes=BinarySize.finite_from_str(capacity),
            used_bytes=BinarySize.finite_from_str(used),
        )

    async def get_quota(self, vfpath):
        report = await run(f"getfattr -n ceph.quota.max_bytes {vfpath}")
        if len(report.split()) != 6:
            raise ExecutionError("ceph quota report output is in unexpected format")
        _, quota = report.split("=")
        quota = quota.replace('"', "")
        return int(quota)

    async def set_quota(self, vfpath, size_bytes) -> None:
        await run(f"setfattr -n ceph.quota.max_bytes -v {int(size_bytes)} {vfpath}")
