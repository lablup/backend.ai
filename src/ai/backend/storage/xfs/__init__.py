import asyncio
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    Optional,
)

import aiofiles
import aiofiles.os

from ai.backend.common.lock import FileLock
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import QuotaScopeID
from ai.backend.storage.abc import CAP_QUOTA, CAP_VFOLDER

from ..abc import AbstractQuotaModel
from ..exception import InvalidQuotaScopeError, NotEmptyError
from ..subproc import run
from ..types import (
    QuotaConfig,
    QuotaUsage,
)
from ..vfs import BaseQuotaModel, BaseVolume

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

LOCK_FILE = Path("/tmp/backendai-xfs-file-lock")
Path(LOCK_FILE).touch()


class XfsProjectRegistry:
    file_projects: Path = Path("/etc/projects")
    file_projid: Path = Path("/etc/projid")
    backend: BaseVolume
    name_id_map: Dict[str, int] = dict()
    project_id_pool: List[int] = list()

    async def init(self, backend: BaseVolume) -> None:
        self.backend = backend

    async def read_project_info(self):
        def _read_projid_file():
            return self.file_projid.read_text()

        # TODO: how to handle if /etc/proj* files are deleted by external reason?
        # TODO: do we need to use /etc/proj* files to enlist the project information?
        if self.file_projid.is_file():
            project_id_pool = []
            self.name_id_map = {}
            loop = asyncio.get_running_loop()
            raw_projid = await loop.run_in_executor(None, _read_projid_file)
            for line in raw_projid.splitlines():
                proj_name, proj_id = line.split(":")[:2]
                project_id_pool.append(int(proj_id))
                self.name_id_map[proj_name] = int(proj_id)
            self.project_id_pool = sorted(project_id_pool)
        else:
            await run(["sudo", "touch", self.file_projid])
        if not Path(self.file_projects).is_file():
            await run(["sudo", "touch", self.file_projects])

    async def add_project_entry(
        self,
        quota_scope_id: QuotaScopeID,
        qspath: Path,
        *,
        project_id: Optional[int] = None,
    ) -> None:
        if project_id is None:
            project_id = self.get_free_project_id()

        temp_name_projects = ""
        temp_name_projid = ""

        def _create_temp_files():
            nonlocal temp_name_projects, temp_name_projid
            _tmp_projects = NamedTemporaryFile(delete=False)
            _tmp_projid = NamedTemporaryFile(delete=False)
            try:
                _projects_content = Path(self.file_projects).read_text()
                if _projects_content.strip() != "" and not _projects_content.endswith(
                    "\n",
                ):
                    _projects_content += "\n"
                _projects_content += f"{project_id}:{qspath}\n"
                _tmp_projects.write(_projects_content.encode("ascii"))
                temp_name_projects = _tmp_projects.name

                _projid_content = Path(self.file_projid).read_text()
                if _projid_content.strip() != "" and not _projid_content.endswith("\n"):
                    _projid_content += "\n"
                _projid_content += f"{quota_scope_id.pathname}:{project_id}\n"
                _tmp_projid.write(_projid_content.encode("ascii"))
                temp_name_projid = _tmp_projid.name
            finally:
                _tmp_projects.close()
                _tmp_projid.close()

        def _delete_temp_files():
            try:
                os.unlink(temp_name_projects)
            except FileNotFoundError:
                pass
            try:
                os.unlink(temp_name_projid)
            except FileNotFoundError:
                pass

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, _create_temp_files)
            await run(["sudo", "cp", "-rp", temp_name_projects, self.file_projects])
            await run(["sudo", "cp", "-rp", temp_name_projid, self.file_projid])
        finally:
            await loop.run_in_executor(None, _delete_temp_files)

    async def remove_project_entry(self, quota_scope_id: QuotaScopeID) -> None:
        await run(["sudo", "sed", "-i.bak", f"/{quota_scope_id.pathname}/d", self.file_projects])
        await run(["sudo", "sed", "-i.bak", f"/{quota_scope_id.pathname}/d", self.file_projid])

    def get_free_project_id(self) -> int:
        """
        Get the next project_id, which is the smallest unused integer.
        """
        project_id = -1
        for i in range(len(self.project_id_pool) - 1):
            if self.project_id_pool[i] + 1 != self.project_id_pool[i + 1]:
                project_id = self.project_id_pool[i] + 1
                break
        if len(self.project_id_pool) == 0:
            project_id = 1
        if project_id == -1:
            project_id = self.project_id_pool[-1] + 1
        return project_id


class XFSProjectQuotaModel(BaseQuotaModel):
    """
    Implements the quota scope model using XFS projects.
    """

    def __init__(
        self,
        mount_path: Path,
        project_registry: XfsProjectRegistry,
    ) -> None:
        super().__init__(mount_path)
        self.project_registry = project_registry
        stat_vfs = os.statvfs(mount_path)
        self.block_size = stat_vfs.f_bsize

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        try:
            if options is None:
                # Set the limit as the filesystem size
                vfs_stat = os.statvfs(self.mount_path)
                options = QuotaConfig(vfs_stat.f_blocks * self.block_size)
            async with FileLock(LOCK_FILE):
                log.info(
                    "creating project quota (qs:{}, q:{})",
                    quota_scope_id,
                    (options.limit_bytes if options else None),
                )
                await aiofiles.os.makedirs(qspath)
                await self.project_registry.read_project_info()
                await self.project_registry.add_project_entry(quota_scope_id, qspath)
                await self.project_registry.read_project_info()
        except (asyncio.CancelledError, asyncio.TimeoutError):
            log.exception("quota-scope creation timeout")
            raise
        except Exception:
            log.exception("quota-scope creation error")
            raise
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> Optional[QuotaUsage]:
        if not self.mangle_qspath(quota_scope_id).exists():
            return None
        full_report = await run(
            # -p: project quota only
            # -b: as number of blocks
            # -N: without header
            ["sudo", "xfs_quota", "-x", "-c", "report -p -b -N", self.mount_path],
        )
        print(full_report)
        for line in full_report.splitlines():
            if quota_scope_id.pathname in line:
                report = line
                break
        else:
            raise RuntimeError(f"unknown xfs project ID: {quota_scope_id.pathname}")
        if len(report.split()) != 6:
            raise ValueError("unexpected format for xfs_quota report")
        _, used_kbs, _, hard_limit_kbs, _, _ = report.split()
        # By default, report command displays the sizes in the 1 KiB unit.
        used_bytes = int(used_kbs) * 1024
        hard_limit_bytes = int(hard_limit_kbs) * 1024
        return QuotaUsage(used_bytes, hard_limit_bytes)

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        # This will annotate all entries under the quota scope tree as a part of the project.
        await run(
            [
                "sudo",
                "xfs_quota",
                "-x",
                "-c",
                f"project -s {quota_scope_id.pathname}",
                self.mount_path,
            ],
        )
        # bsoft, bhard accepts bytes or binary-prefixed numbers.
        await run(
            [
                "sudo",
                "xfs_quota",
                "-x",
                "-c",
                (
                    "limit -p"
                    f" bsoft={config.limit_bytes} bhard={config.limit_bytes} {quota_scope_id.pathname}"
                ),
                self.mount_path,
            ],
        )

    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        raise InvalidQuotaScopeError(
            "Unsetting folder limit without removing quota scope is not possible for this backend"
        )

    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        async with FileLock(LOCK_FILE):
            await self.project_registry.read_project_info()
            await self.project_registry.remove_project_entry(quota_scope_id)
            await self.project_registry.read_project_info()
            await aiofiles.os.rmdir(qspath)


class XfsVolume(BaseVolume):
    """
    XFS volume backend. XFS natively supports per-directory quota through
    the project qutoa. To enalbe project quota, the XFS volume should be
    mounted with `-o pquota` option.

    This backend requires `root` or no password `sudo` permission to run
    `xfs_quota` command and write to `/etc/projects` and `/etc/projid`.
    """

    name = "xfs"

    project_registry: XfsProjectRegistry

    async def init(self) -> None:
        self.project_registry = XfsProjectRegistry()
        await self.project_registry.init(self)
        await super().init()

    async def create_quota_model(self) -> AbstractQuotaModel:
        return XFSProjectQuotaModel(
            self.mount_path,
            self.project_registry,
        )

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA])
