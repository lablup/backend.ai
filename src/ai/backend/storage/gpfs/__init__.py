import json
import logging
from pathlib import Path
from typing import Any, FrozenSet, Mapping, Optional

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID

from ..abc import (
    CAP_FAST_FS_SIZE,
    CAP_METRIC,
    CAP_QUOTA,
    CAP_VFOLDER,
    AbstractFSOpModel,
    AbstractQuotaModel,
    QuotaConfig,
    QuotaUsage,
)
from ..types import CapacityUsage, FSPerfMetric
from ..vfs import BaseFSOpModel, BaseQuotaModel, BaseVolume
from .exceptions import GPFSNoMetricError
from .gpfs_client import GPFSAPIClient

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class GPFSQuotaModel(BaseQuotaModel):
    def __init__(
        self,
        mount_path: Path,
        api_client: GPFSAPIClient,
        fs: str,
        gpfs_owner: str,
    ) -> None:
        super().__init__(mount_path)
        self.api_client = api_client
        self.fs = fs
        self.gpfs_owner = gpfs_owner

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await self.api_client.create_fileset(
            self.fs,
            quota_scope_id.pathname,
            path=qspath,
            owner=self.gpfs_owner,
        )
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    async def update_quota_scope(self, quota_scope_id: QuotaScopeID, config: QuotaConfig) -> None:
        await self.api_client.set_quota(self.fs, quota_scope_id.pathname, config.limit_bytes)

    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> Optional[QuotaUsage]:
        if not self.mangle_qspath(quota_scope_id).exists():
            return None

        quotas = await self.api_client.list_fileset_quotas(self.fs, quota_scope_id.pathname)
        custom_defined_quotas = [q for q in quotas if not q.isDefaultQuota]
        if len(custom_defined_quotas) == 0:
            return QuotaUsage(-1, -1)
        quota_info = custom_defined_quotas[0]
        # The units are kilobytes (ref: )
        return QuotaUsage(
            used_bytes=quota_info.blockUsage * 1024 if quota_info.blockUsage is not None else -1,
            limit_bytes=quota_info.blockLimit * 1024 if quota_info.blockLimit is not None else -1,
        )

    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        await self.api_client.remove_quota(self.fs, quota_scope_id.pathname)

    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        await self.api_client.remove_fileset(self.fs, quota_scope_id.pathname)


class GPFSOpModel(BaseFSOpModel):
    def __init__(
        self,
        mount_path: Path,
        scandir_limit: int,
        api_client: GPFSAPIClient,
        fs: str,
    ) -> None:
        super().__init__(mount_path, scandir_limit)
        self.api_client = api_client
        self.fs = fs

    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        await self.api_client.copy_folder(
            self.fs,
            src_path,
            self.fs,
            dst_path,
        )


class GPFSVolume(BaseVolume):
    name = "gpfs"
    api_client: GPFSAPIClient

    fs: str

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
        verify_ssl = self.config.get("gpfs_verify_ssl", False)
        self.api_client = GPFSAPIClient(
            self.config["gpfs_endpoint"],
            self.config["gpfs_username"],
            self.config["gpfs_password"],
            # follows ssl parameter on https://docs.aiohttp.org/en/v3.7.3/client_reference.html
            ssl=False if not verify_ssl else None,
        )
        self.fs = self.config["gpfs_fs_name"]
        self.gpfs_owner = self.config.get("gpfs_owner", "1000:1000")

    async def init(self) -> None:
        await super().init()

    async def create_quota_model(self) -> AbstractQuotaModel:
        return GPFSQuotaModel(
            self.mount_path,
            self.api_client,
            self.fs,
            self.gpfs_owner,
        )

    async def create_fsop_model(self) -> AbstractFSOpModel:
        return GPFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
            self.api_client,
            self.fs,
        )

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_FAST_FS_SIZE, CAP_VFOLDER, CAP_QUOTA, CAP_METRIC])

    async def get_hwinfo(self) -> HardwareMetadata:
        nodes = await self.api_client.list_nodes()
        invalid_status = ["FAILED", "DEGRADED", "ERROR"]
        health_status = "HEALTHY"

        for node in nodes:
            if health_status == "ERROR":
                break
            node_health_statuses = await self.api_client.get_node_health(node)
            for status in node_health_statuses:
                if status.state in invalid_status:
                    health_status = status

        match health_status:
            case "HEALTHY":
                status = "healthy"
            case "DEGRADED":
                status = "degraded"
            case _:
                status = "unavailable"
        cluster_info = await self.api_client.get_cluster_info()
        quotas = await self.api_client.list_quotas(self.fs)
        return {
            "status": status,
            "status_info": None,
            "metadata": {
                "quota": json.dumps([q.to_json() for q in quotas]),
                "cluster_info": json.dumps(cluster_info),
            },
        }

    async def get_fs_usage(self) -> CapacityUsage:
        storage_pools = await self.api_client.list_fs_pools(self.fs)
        free, total = 0, 0
        for _pool in storage_pools:
            pool = await self.api_client.get_fs_pool(self.fs, _pool.storagePoolName)
            if pool.totalDataInKB is None or pool.freeDataInKB is None:
                continue
            total += pool.totalDataInKB
            free += pool.freeDataInKB
        return CapacityUsage(
            used_bytes=BinarySize(total - free) * 1024,
            capacity_bytes=BinarySize(total) * 1024,
        )

    async def get_performance_metric(self) -> FSPerfMetric:
        # ref: https://www.ibm.com/docs/en/spectrum-scale/5.0.3?topic=2-perfmondata-get
        query = (
            "metrics "
            "avg(gpfs_ns_read_ops),"
            "avg(gpfs_ns_write_ops),"
            "avg(gpfs_ns_bytes_read),"
            "avg(gpfs_ns_bytes_written),"
            "avg(gpfs_ns_max_disk_wait_rd),"
            "avg(gpfs_ns_max_disk_wait_wr) "
            "last 1 "
            "bucket_size 10"
        )
        try:
            metrics = await self.api_client.get_metric(query)
            latest_metric = metrics["performanceData"]["rows"][-1]["values"]
        except (KeyError, IndexError):
            raise GPFSNoMetricError
        return FSPerfMetric(
            iops_read=latest_metric[0] or 0,
            iops_write=latest_metric[1] or 0,
            io_bytes_read=latest_metric[2] or 0,
            io_bytes_write=latest_metric[3] or 0,
            io_usec_read=latest_metric[4] or 0,
            io_usec_write=latest_metric[5] or 0,
        )
