from __future__ import annotations

# from contextlib import aclosing
import json
from typing import FrozenSet
from uuid import UUID

from ai.backend.common.types import BinarySize, HardwareMetadata

from ..abc import CAP_METRIC, CAP_VFHOST_QUOTA, CAP_VFOLDER
from ..types import FSPerfMetric, FSUsage
from ..vfs import BaseVolume
from .dellemc_client import DellEMCClient
from .dellemc_quota_manager import QuotaManager
from .exceptions import DellNoMetricError


class DellEMCVolume(BaseVolume):
    endpoint: str
    dell_admin: str
    dell_password: str

    async def init(self) -> None:
        self.endpoint = self.config["dell_endpoint"]
        self.dell_admin = self.config["dell_admin"]
        self.dell_password = str(self.config["dell_password"])
        self.dell_api_version = self.config["dell_api_version"]
        self.dell_system_name = self.config["dell_system_name"]

        self.dellEMC_client = DellEMCClient(
            str(self.endpoint),
            self.dell_admin,
            self.dell_password,
            api_version=self.dell_api_version,
            system_name=self.dell_system_name,
        )

        self.quota_manager = QuotaManager(
            str(self.endpoint),
            self.dell_admin,
            self.dell_password,
            api_version=self.dell_api_version,
        )

    async def shutdown(self) -> None:
        await self.dellEMC_client.aclose()
        await self.quota_manager.aclose()

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_VFHOST_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        raw_metadata = await self.dellEMC_client.get_metadata()
        quotas = await self.quota_manager.list_all_quota()
        metadata = {"quotas": json.dumps(quotas), **raw_metadata}
        return {"status": "healthy", "status_info": None, "metadata": {**metadata}}

    async def get_fs_usage(self) -> FSUsage:
        usage = await self.dellEMC_client.get_usage()
        return FSUsage(
            capacity_bytes=usage["capacity_bytes"],
            used_bytes=usage["used_bytes"],
        )

    async def get_quota_id(self):
        quotas = await self.quota_manager.list_all_quota()
        quota_id = []
        for quota in quotas:
            quota_id.append(quota["id"])
        return quota_id

    async def get_quota(self, vfid: UUID) -> BinarySize:
        raise NotImplementedError

    async def get_drive_stats(self):
        try:
            resp = await self.dellEMC_client.get_drive_stats()
            return resp
        except KeyError:
            raise DellNoMetricError

    async def get_protocol_stats(self):
        try:
            resp = await self.dellEMC_client.get_protocol_stats()
            return resp
        except KeyError:
            raise DellNoMetricError

    async def get_system_stats(self):
        try:
            resp = await self.dellEMC_client.get_system_stats()
            return resp
        except KeyError:
            raise DellNoMetricError

    async def get_workload_stats(self):
        try:
            resp = await self.dellEMC_client.get_workload_stats()
            return resp
        except KeyError:
            raise DellNoMetricError

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

    async def create_quota(self, path, type):
        quota_id = self.quota_manager.create_quota(path, type)
        return quota_id
