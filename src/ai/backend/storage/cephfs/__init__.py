import asyncio
import os
import shutil
from pathlib import Path
from typing import Any, Dict, FrozenSet, List

import aiofiles.os

from ai.backend.common.types import BinarySize, QuotaScopeID
from ai.backend.storage.exception import QuotaScopeNotFoundError

from ..abc import CAP_FAST_SIZE, CAP_QUOTA, CAP_VFOLDER, AbstractFSOpModel, AbstractQuotaModel
from ..subproc import run
from ..types import CapacityUsage, Optional, QuotaConfig, QuotaUsage, TreeUsage
from ..vfs import BaseFSOpModel, BaseQuotaModel, BaseVolume


class CephDirQuotaModel(BaseQuotaModel):
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.makedirs(qspath)
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> Optional[QuotaUsage]:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            return None
        loop = asyncio.get_running_loop()

        def read_attrs() -> tuple[int, int]:
            used_bytes = int(os.getxattr(qspath, "ceph.dir.rbytes").decode())  # type: ignore[attr-defined]
            try:
                limit_bytes = int(os.getxattr(qspath, "ceph.quota.max_bytes").decode())  # type: ignore[attr-defined]
            except OSError as e:
                match e.errno:
                    case 61:
                        limit_bytes = 0
                    case _:
                        limit_bytes = -1  # unset
            return used_bytes, limit_bytes

        # without type: ignore mypy will raise error when trying to run on macOS
        # because os.getxattr() exists only for linux
        used_bytes, limit_bytes = await loop.run_in_executor(
            None,
            read_attrs,
        )
        return QuotaUsage(used_bytes=used_bytes, limit_bytes=limit_bytes)

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            raise QuotaScopeNotFoundError

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            # without type: ignore mypy will raise error when trying to run on macOS
            # because os.setxattr() exists only for linux
            lambda: os.setxattr(  # type: ignore[attr-defined]
                qspath, "ceph.quota.max_bytes", str(int(config.limit_bytes)).encode()
            ),
        )

    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            raise QuotaScopeNotFoundError

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            # without type: ignore mypy will raise error when trying to run on macOS
            # because os.setxattr() exists only for linux
            lambda: os.setxattr(qspath, "ceph.quota.max_bytes", b"0"),  # type: ignore[attr-defined]
        )


class CephFSOpModel(BaseFSOpModel):
    async def scan_tree_usage(self, path: Path) -> TreeUsage:
        loop = asyncio.get_running_loop()
        raw_reports = await loop.run_in_executor(
            None,
            lambda: (
                os.getxattr(path, "ceph.dir.rentries"),  # type: ignore[attr-defined]
                os.getxattr(path, "ceph.dir.rbytes"),  # type: ignore[attr-defined]
            ),
        )
        file_count = int(raw_reports[0].strip().decode())
        used_bytes = int(raw_reports[1].strip().decode())
        return TreeUsage(file_count=file_count, used_bytes=used_bytes)

    async def scan_tree_size(self, path: Path) -> BinarySize:
        loop = asyncio.get_running_loop()
        raw_report = await loop.run_in_executor(
            None,
            lambda: os.getxattr(path, "ceph.dir.rbytes"),  # type: ignore[attr-defined]
        )
        return BinarySize(raw_report.strip().decode())


class CephFSVolume(BaseVolume):
    name = "cephfs"
    loop: asyncio.AbstractEventLoop
    registry: Dict[str, int]
    project_id_pool: List[int]

    async def init(self) -> None:
        try:
            await run([b"ceph", b"--version"])
        except FileNotFoundError:
            raise RuntimeError("Ceph is not installed. ")
        await super().init()

    async def create_quota_model(self) -> AbstractQuotaModel:
        return CephDirQuotaModel(self.mount_path)

    async def create_fsop_model(self) -> AbstractFSOpModel:
        return CephFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
        )

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA, CAP_FAST_SIZE])

    async def get_fs_usage(self) -> CapacityUsage:
        (total, used, _) = await asyncio.get_running_loop().run_in_executor(
            None,
            shutil.disk_usage,
            self.mount_path,
        )
        return CapacityUsage(
            used_bytes=used,
            capacity_bytes=total,
        )
