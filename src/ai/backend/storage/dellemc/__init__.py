from __future__ import annotations

from pathlib import Path
from typing import Any, FrozenSet, Optional

import aiofiles.os

from ai.backend.common.types import HardwareMetadata, QuotaScopeID

from ..abc import CAP_FAST_FS_SIZE, CAP_METRIC, CAP_QUOTA, CAP_VFOLDER, AbstractQuotaModel
from ..exception import NotEmptyError
from ..types import CapacityUsage, FSPerfMetric, QuotaConfig, QuotaUsage
from ..vfs import BaseQuotaModel, BaseVolume
from .exceptions import DellNoMetricError
from .onefs_client import OneFSClient, QuotaThresholds, QuotaTypes


class DellEMCOneFSQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        *,
        api_client: OneFSClient,
    ) -> None:
        super().__init__(mount_path)
        self.api_client = api_client

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
        quota_id_path = qspath / ".quota_id"
        if quota_id_path.exists():
            quota_id = quota_id_path.read_text()
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
        quota_id_path = qspath / ".quota_id"
        if quota_id_path.exists():
            quota_id = quota_id_path.read_text()
            await self.api_client.update_quota(
                quota_id,
                QuotaThresholds(hard=config.limit_bytes, soft=config.limit_bytes),
            )
        else:
            result = await self.api_client.create_quota(
                qspath,
                QuotaTypes.DIRECTORY,
                QuotaThresholds(hard=config.limit_bytes, soft=config.limit_bytes),
            )
            quota_id_path.write_text(result["id"])

    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id_path = qspath / ".quota_id"
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        if quota_id_path.exists():
            quota_id = quota_id_path.read_text()
            await self.api_client.delete_quota(quota_id)
            await aiofiles.os.remove(quota_id_path)

    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id_path = qspath / ".quota_id"
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise NotEmptyError(quota_scope_id)
        if quota_id_path.exists():
            quota_id = quota_id_path.read_text()
            await self.api_client.delete_quota(quota_id)
            await aiofiles.os.remove(quota_id_path)
        await aiofiles.os.rmdir(qspath)


class DellEMCOneFSVolume(BaseVolume):
    name = "dellemc-onefs"
    endpoint: str
    dell_admin: str
    dell_password: str

    async def init(self) -> None:
        self.endpoint = self.config["dell_endpoint"]
        self.dell_admin = self.config["dell_admin"]
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
        return DellEMCOneFSQuotaModel(self.mount_path, api_client=self.api_client)

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
            capacity_bytes=usage["capacity_bytes"],
            used_bytes=usage["used_bytes"],
        )

    async def get_performance_metric(self) -> FSPerfMetric:
        try:
            protocol_stats = await self.get_protocol_stats()
            workload = await self.get_workload_stats()
        except (KeyError, IndexError):
            raise DellNoMetricError
        return FSPerfMetric(
            iops_read=protocol_stats["disk"]["iops"] or 0,
            iops_write=0,  # Dell does not support IOPS Read/Write, They support only IOPS.
            io_bytes_read=protocol_stats["onefs"]["out"] or 0,
            io_bytes_write=protocol_stats["onefs"]["in"] or 0,
            io_usec_read=workload["latency_write"] or 0,
            io_usec_write=workload["latency_read"] or 0,
        )

    # -- Custom Methods --

    async def get_drive_stats(self):
        try:
            resp = await self.api_client.get_drive_stats()
            return resp
        except KeyError:
            raise DellNoMetricError

    async def get_protocol_stats(self):
        try:
            resp = await self.api_client.get_protocol_stats()
            return resp
        except KeyError:
            raise DellNoMetricError

    async def get_system_stats(self):
        try:
            resp = await self.api_client.get_system_stats()
            return resp
        except KeyError:
            raise DellNoMetricError

    async def get_workload_stats(self):
        try:
            resp = await self.api_client.get_workload_stats()
            return resp
        except KeyError:
            raise DellNoMetricError
