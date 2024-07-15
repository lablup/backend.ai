import asyncio
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Final, FrozenSet, Mapping

import aiofiles
import aiofiles.os

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import QuotaScopeID
from ai.backend.storage.exception import QuotaScopeAlreadyExists, QuotaScopeNotFoundError

from ..abc import CAP_QUOTA, CAP_VFOLDER, AbstractQuotaModel
from ..subproc import run
from ..types import Optional, QuotaConfig, QuotaUsage
from ..vfs import BaseQuotaModel, BaseVolume

FIRST_PROJECT_ID: Final = 100
PROJECT_MAIN_ID_KEY: Final = "ddn/main-project-id"
PROJECT_ID_FILE_NAME: Final = "project_id"


def _byte_to_kilobyte(byte: int) -> int:
    return byte // 1024


def _kilobyte_to_byte(kilobyte: int) -> int:
    return kilobyte * 1024


class EXAScalerQuotaModel(BaseQuotaModel):
    def __init__(self, mount_path: Path, local_config: Mapping[str, Any], etcd: AsyncEtcd) -> None:
        self.local_config = local_config
        self.etcd = etcd
        super().__init__(mount_path)
        return

    async def _read_project_id(self, pid_file_path: str | Path) -> int | None:
        def _read():
            try:
                with open(pid_file_path, "r") as f:
                    return int(f.read())
            except FileNotFoundError:
                return None

        return await asyncio.get_running_loop().run_in_executor(None, _read)

    async def _write_project_id(self, pid: int, pid_file_path: str | Path) -> None:
        def _write():
            with open(pid_file_path, "w") as f:
                f.write(str(pid))

        await asyncio.get_running_loop().run_in_executor(None, _write)

    async def _read_main_project_id(self) -> int:
        raw_val = await self.etcd.get(PROJECT_MAIN_ID_KEY)
        if raw_val is None:
            val = int(FIRST_PROJECT_ID)
        else:
            val = int(raw_val)
        await self.etcd.put(PROJECT_MAIN_ID_KEY, str(val + 1))
        return val

    async def _set_quota_by_project(self, pid: int, path: Path, options: QuotaConfig) -> None:
        quota_limit = _byte_to_kilobyte(options.limit_bytes)  # default unit for DDN quota is KB
        try:
            await run([
                b"sudo",
                b"lfs",
                b"setquota",
                b"-p",
                str(pid),
                f"-B{quota_limit}",
                path,
            ])
        except CalledProcessError as e:
            raise RuntimeError(f"'lfs setquota -p {pid}' command failed: {e.stderr}")

    async def _unset_quota_by_project(self, pid: int, path: Path) -> None:
        await self._set_quota_by_project(pid, path, QuotaConfig(0))

    async def _get_quota_by_project(self, pid: int, qspath: Path) -> QuotaUsage | None:
        proc = await asyncio.create_subprocess_exec(
            b"lfs",
            b"quota",
            b"-p",
            str(pid),
            str(qspath),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            assert proc.stdout is not None
            next_line_is_quota = False
            while True:
                try:
                    raw = await proc.stdout.readline()
                    if not raw:
                        break
                    line = raw.decode()
                except asyncio.IncompleteReadError:
                    break
                words = line.split()
                if next_line_is_quota:
                    raw_used_bytes, hard_limit = words[0], int(words[2])
                    # words[1] is soft_limit
                    if hard_limit == 0:
                        return None
                    if raw_used_bytes.endswith("*"):
                        raw_used_bytes = raw_used_bytes[:-1]
                    used_bytes = _kilobyte_to_byte(int(raw_used_bytes))
                    return QuotaUsage(
                        used_bytes=used_bytes, limit_bytes=_kilobyte_to_byte(hard_limit)
                    )
                if Path(words[0]) == qspath:
                    next_line_is_quota = True
                    continue
            return None
        finally:
            await proc.wait()

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        pid_path = qspath / PROJECT_ID_FILE_NAME
        try:
            await aiofiles.os.makedirs(qspath)
        except FileExistsError:
            pass
        project_id = await self._read_project_id(pid_path)
        if project_id is None:
            main_pid = await self._read_main_project_id()
            project_id = main_pid + 1
            await self._write_project_id(project_id, pid_path)
        else:
            quota_usage = await self._get_quota_by_project(project_id, qspath)
            if quota_usage is not None:
                raise QuotaScopeAlreadyExists

        # Set projectID to the directory
        try:
            await run([
                b"sudo",
                b"lfs",
                b"project",
                b"-p",
                str(project_id),
                b"-r",
                b"-s",
                str(qspath),
            ])
        except CalledProcessError as e:
            raise RuntimeError(f"'lfs project -p {project_id}' command failed: {e.stderr}")

        if options is not None:
            await self._set_quota_by_project(project_id, qspath, options)

    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> QuotaUsage | None:
        """
        $ lfs quota -p <projectId> <fs_mount_point>

        Disk quotas for prj <PID> (pid <PID>):
        Filesystem  kbytes   quota   limit   grace   files   quota   limit   grace
        /mnt/lufs01/vfroot/test
                    1004       0       2048       -       2       0       0       -
        pid <PID> is using default file quota setting

        ---

        `kbytes` is quota usage. `quota` is soft limit and `limit` is hard limit.
        It will remove files after the `grace` if you exceed soft limit.
        """

        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            return None
        pid_path = qspath / PROJECT_ID_FILE_NAME
        if (pid := await self._read_project_id(pid_path)) is None:
            return None

        return await self._get_quota_by_project(pid, qspath)

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        pid_path = qspath / PROJECT_ID_FILE_NAME
        pid = await self._read_project_id(pid_path)
        if pid is None:
            raise QuotaScopeNotFoundError
        await self._set_quota_by_project(pid, qspath, config)

    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        pid_path = qspath / PROJECT_ID_FILE_NAME
        pid = await self._read_project_id(pid_path)
        if pid is None:
            raise QuotaScopeNotFoundError
        await self._unset_quota_by_project(pid, qspath)

    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        await self.unset_quota(quota_scope_id)
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.rmdir(qspath)


class EXAScalerFSVolume(BaseVolume):
    name = "exascaler"

    async def create_quota_model(self) -> AbstractQuotaModel:
        return EXAScalerQuotaModel(self.mount_path, self.local_config, self.etcd)

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA])
