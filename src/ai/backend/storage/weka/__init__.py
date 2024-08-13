import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, FrozenSet, Mapping, Optional

import aiofiles.os

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import HardwareMetadata, QuotaConfig, QuotaScopeID

from ..abc import CAP_FAST_FS_SIZE, CAP_METRIC, CAP_QUOTA, CAP_VFOLDER, AbstractQuotaModel
from ..types import CapacityUsage, FSPerfMetric, QuotaUsage
from ..vfs import BaseQuotaModel, BaseVolume
from .exceptions import WekaAPIError, WekaInitError, WekaNoMetricError, WekaNotFoundError
from .weka_client import WekaAPIClient

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class WekaQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        fs_uid: str,
        api_client: WekaAPIClient,
    ) -> None:
        super().__init__(mount_path)
        self.fs_uid = fs_uid
        self.api_client = api_client

    async def _get_inode_id(self, path: Path) -> int:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: os.stat(path).st_ino,
        )

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.makedirs(qspath)
        assert self.fs_uid is not None
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    async def update_quota_scope(self, quota_scope_id: QuotaScopeID, config: QuotaConfig) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        inode_id = await self._get_inode_id(qspath)
        qs_relpath = qspath.relative_to(self.mount_path).as_posix()
        if not qs_relpath.startswith("/"):
            qs_relpath = "/" + qs_relpath
        await self.api_client.set_quota_v1(
            qs_relpath, inode_id, soft_limit=config.limit_bytes, hard_limit=config.limit_bytes
        )

    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> Optional[QuotaUsage]:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            return None

        inode_id = await self._get_inode_id(qspath)
        quota = await self.api_client.get_quota(self.fs_uid, inode_id)
        return QuotaUsage(
            used_bytes=quota.used_bytes if quota.used_bytes is not None else -1,
            limit_bytes=quota.hard_limit if quota.hard_limit is not None else -1,
        )

    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        inode_id = await self._get_inode_id(qspath)
        try:
            await self.api_client.remove_quota(self.fs_uid, inode_id)
        except WekaNotFoundError:
            pass

    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        inode_id = await self._get_inode_id(qspath)
        try:
            await self.api_client.remove_quota(self.fs_uid, inode_id)
        except WekaNotFoundError:
            pass
        await aiofiles.os.rmdir(qspath)


class WekaVolume(BaseVolume):
    api_client: WekaAPIClient

    name = "weka"

    _fs_uid: str

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispathcer: EventDispatcher,
        event_producer: EventProducer,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            local_config,
            mount_path,
            etcd=etcd,
            options=options,
            event_dispathcer=event_dispathcer,
            event_producer=event_producer,
        )
        ssl_verify = self.config.get("weka_verify_ssl", False)
        self.api_client = WekaAPIClient(
            self.config["weka_endpoint"],
            self.config["weka_username"],
            self.config["weka_password"],
            self.config["weka_organization"],
            ssl=ssl_verify,
        )

    async def init(self) -> None:
        for fs in await self.api_client.list_fs():
            if fs.name == self.config["weka_fs_name"]:
                self._fs_uid = fs.uid
                break
        else:
            raise WekaInitError(f"FileSystem {self.config['weka_fs_name']} not found")
        await super().init()

    async def create_quota_model(self) -> AbstractQuotaModel:
        return WekaQuotaModel(self.mount_path, self._fs_uid, self.api_client)

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA, CAP_METRIC, CAP_FAST_FS_SIZE])

    async def get_hwinfo(self) -> HardwareMetadata:
        assert self._fs_uid is not None
        health_status = (await self.api_client.check_health()).lower()
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

    async def get_fs_usage(self) -> CapacityUsage:
        assert self._fs_uid is not None
        fs = await self.api_client.get_fs(self._fs_uid)
        return CapacityUsage(
            capacity_bytes=fs.total_budget,
            used_bytes=fs.used_total,
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
