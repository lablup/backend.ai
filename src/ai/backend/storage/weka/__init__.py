import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path, PurePath
from typing import Any, FrozenSet, Mapping
from uuid import UUID

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize, HardwareMetadata
from ai.backend.storage.abc import CAP_METRIC, CAP_QUOTA, CAP_VFOLDER
from ai.backend.storage.types import FSPerfMetric, FSUsage, VFolderCreationOptions
from ai.backend.storage.vfs import BaseVolume

from .exceptions import WekaAPIError, WekaInitError, WekaNoMetricError, WekaNotFoundError
from .weka_client import WekaAPIClient

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class WekaVolume(BaseVolume):

    api_client: WekaAPIClient

    _fs_uid: str

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        fsprefix: PurePath = None,
        options: Mapping[str, Any] = None,
    ) -> None:
        super().__init__(local_config, mount_path, fsprefix=fsprefix, options=options)
        ssl_verify = self.config.get("weka_verify_ssl", False)
        self.api_client = WekaAPIClient(
            self.config["weka_endpoint"],
            self.config["weka_username"],
            self.config["weka_password"],
            self.config["weka_organization"],
            ssl=ssl_verify,
        )

    async def init(self) -> None:
        await super().init()
        for fs in await self.api_client.list_fs():
            if fs.name == self.config["weka_fs_name"]:
                self._fs_uid = fs.uid
                return
        else:
            raise WekaInitError(f"FileSystem {fs.name} not found")

    async def _get_inode_id(self, path: Path) -> int:
        return await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: os.stat(path).st_ino,
        )

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        assert self._fs_uid is not None
        health_status = await self.api_client.check_health()
        if health_status == "ok":
            health_status = "healthy"

        try:
            cluster_info = await self.api_client.get_cluster_info()
            quotas = await self.api_client.list_quotas(self._fs_uid)
            return {
                "status": health_status,
                "status_info": None,
                "metadata": {
                    "quota": json.dumps([q.to_json() for q in quotas]),
                    "cluster_info": json.dumps(cluster_info),
                },
            }
        except WekaAPIError:
            return {
                "status": health_status,
                "status_info": None,
                "metadata": {},
            }

    async def get_fs_usage(self) -> FSUsage:
        assert self._fs_uid is not None
        fs = await self.api_client.get_fs(self._fs_uid)
        return FSUsage(
            fs.total_budget,
            fs.used_total,
        )

    async def get_performance_metric(self) -> FSPerfMetric:
        start_time = datetime.now().replace(second=0, microsecond=0) - timedelta(
            minutes=1,
        )

        try:
            metrics = await self.api_client.get_metric(
                [
                    "ops.READS",
                    "ops.WRITES",
                    "ops.READ_BYTES",
                    "ops.WRITE_BYTES",
                    "ops.READ_LATENCY",
                    "ops.WRITE_LATENCY",
                ],
                start_time,
            )
            latest_metric = metrics["ops"][-1]["stats"]
        except KeyError:
            raise WekaNoMetricError
        except IndexError:
            raise WekaNoMetricError
        return FSPerfMetric(
            iops_read=latest_metric["READS"],
            iops_write=latest_metric["WRITES"],
            io_bytes_read=latest_metric["READ_BYTES"],
            io_bytes_write=latest_metric["WRITE_BYTES"],
            io_usec_read=latest_metric["READ_LATENCY"] or 0,
            io_usec_write=latest_metric["WRITE_LATENCY"] or 0,
        )

    async def create_vfolder(
        self,
        vfid: UUID,
        options: VFolderCreationOptions = None,
        *,
        exist_ok: bool = False,
    ) -> None:
        await super().create_vfolder(vfid, options, exist_ok=exist_ok)
        if options is not None and options.quota is not None:
            await self.set_quota(vfid, options.quota)

    async def delete_vfolder(self, vfid: UUID) -> None:
        assert self._fs_uid is not None
        vfpath = self.mangle_vfpath(vfid)
        inode_id = await self._get_inode_id(vfpath)
        try:
            await self.api_client.remove_quota(self._fs_uid, inode_id)
        except WekaNotFoundError:
            pass
        await super().delete_vfolder(vfid)

    async def get_quota(self, vfid: UUID) -> BinarySize:
        assert self._fs_uid is not None
        vfpath = self.mangle_vfpath(vfid)
        inode_id = await self._get_inode_id(vfpath)
        quota = await self.api_client.get_quota(self._fs_uid, inode_id)
        return BinarySize(quota.hard_limit)

    async def set_quota(self, vfid: UUID, size_bytes: BinarySize) -> None:
        assert self._fs_uid is not None
        vfpath = self.mangle_vfpath(vfid)
        inode_id = await self._get_inode_id(vfpath)
        weka_path = vfpath.absolute().as_posix().replace(self.mount_path.absolute().as_posix(), "")
        if not weka_path.startswith("/"):
            weka_path = "/" + weka_path
        await self.api_client.set_quota_v1(weka_path, inode_id, hard_limit=size_bytes)
