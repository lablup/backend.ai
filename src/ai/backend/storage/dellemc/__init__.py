from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, FrozenSet, Optional, cast

import aiofiles.os

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.types import HardwareMetadata, QuotaScopeID

from ..abc import CAP_FAST_FS_SIZE, CAP_METRIC, CAP_QUOTA, CAP_VFOLDER, AbstractQuotaModel
from ..exception import NotEmptyError
from ..types import CapacityUsage, FSPerfMetric, QuotaConfig, QuotaUsage
from ..vfs import BaseQuotaModel, BaseVolume
from .config import config_iv
from .exceptions import DellNoMetricError
from .onefs_client import OneFSClient, QuotaThresholds, QuotaTypes


class DellEMCOneFSQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        *,
        ifs_path: Path,
        api_client: OneFSClient,
    ) -> None:
        super().__init__(mount_path)
        self.ifs_path = ifs_path
        self.api_client = api_client

    async def _set_quota_id(self, qspath: Path, quota_id: str) -> None:
        quota_id_path = qspath / ".quota_id"
        async with aiofiles.open(quota_id_path, "w") as file:
            await file.write(quota_id.rstrip())

    async def _get_quota_id(self, qspath: Path) -> Optional[str]:
        """
        Read OneFS quota id of the given path.
        Return `None` if no quota is set to the path.
        """
        quota_id_path = qspath / ".quota_id"
        if quota_id_path.exists():
            async with aiofiles.open(quota_id_path, "r") as file:
                quota_id = await file.read()
            return quota_id.rstrip()
        else:
            return None

    async def _unset_quota_id(self, qspath: Path) -> None:
        quota_id_path = qspath / ".quota_id"
        if quota_id_path.exists():
            await aiofiles.os.remove(quota_id_path)

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.makedirs(qspath, exist_ok=True)
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> Optional[QuotaUsage]:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id = await self._get_quota_id(qspath)
        if quota_id is not None:
            data = await self.api_client.get_quota(quota_id)
            return QuotaUsage(
                used_bytes=data["usage"]["fslogical"],
                limit_bytes=data["thresholds"]["hard"],
            )
        else:
            return None

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id = await self._get_quota_id(qspath)
        if quota_id is not None:
            await self.api_client.update_quota(
                quota_id,
                QuotaThresholds(
                    hard=config.limit_bytes,
                ),
            )
        else:
            quota_target_path = self.ifs_path / quota_scope_id.pathname
            result = await self.api_client.create_quota(
                quota_target_path,
                QuotaTypes.DIRECTORY,
                QuotaThresholds(
                    hard=config.limit_bytes,
                ),
            )
            await self._set_quota_id(qspath, result["id"])

    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id = await self._get_quota_id(qspath)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            # Check if any directory exists in the quota scope path
            raise NotEmptyError(quota_scope_id)
        if quota_id is not None:
            await self.api_client.delete_quota(quota_id)
            await self._unset_quota_id(qspath)

    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        await self.unset_quota(quota_scope_id)
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.rmdir(qspath)


class DellEMCOneFSVolume(BaseVolume):
    name = "dellemc-onefs"
    endpoint: str
    dell_admin: str
    dell_password: str

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            local_config,
            mount_path,
            etcd=etcd,
            options=options,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
        )
        self.config = cast(Mapping[str, Any], config_iv.check(self.config))
        self.endpoint = self.config["dell_endpoint"]
        self.dell_admin = self.config["dell_username"]
        self.dell_password = str(self.config["dell_password"])
        self.dell_api_version = self.config["dell_api_version"]
        self.dell_system_name = self.config["dell_system_name"]
        self.api_client = OneFSClient(
            str(self.endpoint),
            self.dell_admin,
            self.dell_password,
            api_version=self.dell_api_version,
            system_name=self.dell_system_name,
        )

    async def shutdown(self) -> None:
        await self.api_client.aclose()

    async def create_quota_model(self) -> AbstractQuotaModel:
        ifs_path = Path(self.config["dell_ifs_path"])
        return DellEMCOneFSQuotaModel(
            self.mount_path, api_client=self.api_client, ifs_path=ifs_path
        )

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_FAST_FS_SIZE, CAP_VFOLDER, CAP_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        raw_metadata = await self.api_client.get_metadata()
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {**raw_metadata},
        }

    async def get_fs_usage(self) -> CapacityUsage:
        usage = await self.api_client.get_usage()
        return CapacityUsage(
            capacity_bytes=int(usage["capacity_bytes"]),
            used_bytes=int(usage["used_bytes"]),
        )

    async def get_performance_metric(self) -> FSPerfMetric:
        protocol_stats = await self.get_protocol_stats()
        workload = await self.get_workload_stats()
        return FSPerfMetric(
            iops_read=protocol_stats["disk"]["iops"] or 0,
            iops_write=0,  # Dell does not support IOPS Read/Write, They support only IOPS.
            io_bytes_read=protocol_stats["onefs"]["out"] or 0,
            io_bytes_write=protocol_stats["onefs"]["in"] or 0,
            io_usec_read=workload["latency_write"] or 0,
            io_usec_write=workload["latency_read"] or 0,
        )

    # -- Custom Methods --

    async def get_drive_stats(self) -> Mapping[str, Any]:
        try:
            resp = await self.api_client.get_drive_stats()
            return resp
        except (IndexError, KeyError):
            raise DellNoMetricError

    async def get_protocol_stats(self) -> Mapping[str, Any]:
        try:
            resp = await self.api_client.get_protocol_stats()
            return resp
        except (IndexError, KeyError):
            return {
                "disk": {
                    "iops": 0,
                },
                "onefs": {
                    "out": 0,
                    "in": 0,
                },
            }

    async def get_system_stats(self) -> Mapping[str, Any]:
        try:
            resp = await self.api_client.get_system_stats()
            return resp
        except (IndexError, KeyError):
            raise DellNoMetricError

    async def get_workload_stats(self) -> Mapping[str, Any]:
        try:
            resp = await self.api_client.get_workload_stats()
            return resp
        except (IndexError, KeyError):
            return {
                "latency_write": 0,
                "latency_read": 0,
            }
