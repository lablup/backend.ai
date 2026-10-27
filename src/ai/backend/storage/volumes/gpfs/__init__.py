import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Literal, override

from ai.backend.common.clients.storage_backends.gpfs.client import (
    GPFSAPIClient,
    GPFSAPIClientArgs,
)
from ai.backend.common.configs.volume_status_check import VolumeStatusCheckConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.common.dto.clients.storage_backends.gpfs.request import (
    GPFSCopyFolderRequest,
    GPFSCreateFilesetRequest,
    GPFSSetQuotaRequest,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import BinarySize, HardwareMetadata, QuotaScopeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.types import CapacityUsage, FSPerfMetric, QuotaConfig, QuotaUsage
from ai.backend.storage.volumes.abc import (
    AbstractFSOpModel,
    AbstractQuotaModel,
)
from ai.backend.storage.volumes.vfs import BaseFSOpModel, BaseQuotaModel, BaseVolume
from ai.backend.storage.watcher import WatcherClient

from .exceptions import GPFSNoMetricError

log = StructuredLogger(logging.getLogger(__spec__.name))

_UNHEALTHY_STATES: frozenset[str] = frozenset(["FAILED", "DEGRADED", "ERROR"])


class GPFSQuotaModel(BaseQuotaModel):
    api_client: GPFSAPIClient
    fs: str
    gpfs_owner: str
    _fileset_prefix: str

    def __init__(
        self,
        mount_path: Path,
        api_client: GPFSAPIClient,
        fs: str,
        gpfs_owner: str,
        *,
        fileset_prefix: str | None = None,
    ) -> None:
        super().__init__(mount_path)
        self.api_client = api_client
        self.fs = fs
        self.gpfs_owner = gpfs_owner
        self._fileset_prefix = fileset_prefix or ""

    def _get_fileset_name(self, quota_scope_id: QuotaScopeID) -> str:
        return self._fileset_prefix + quota_scope_id.pathname

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await self.api_client.create_fileset(
            self.fs,
            GPFSCreateFilesetRequest(
                filesetName=self._get_fileset_name(quota_scope_id),
                owner=self.gpfs_owner,
                path=qspath.as_posix(),
            ),
        )
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    @override
    async def update_quota_scope(self, quota_scope_id: QuotaScopeID, config: QuotaConfig) -> None:
        limit_str = str(int(config.limit_bytes))
        await self.api_client.set_quota(
            self.fs,
            GPFSSetQuotaRequest(
                objectName=self._get_fileset_name(quota_scope_id),
                blockSoftLimit=limit_str,
                blockHardLimit=limit_str,
            ),
        )

    @override
    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> QuotaUsage | None:
        if not self.mangle_qspath(quota_scope_id).exists():
            return None

        quotas = await self.api_client.list_fileset_quotas(
            self.fs,
            self._get_fileset_name(quota_scope_id),
        )
        custom_defined_quotas = [q for q in quotas if not q.isDefaultQuota]
        if len(custom_defined_quotas) == 0:
            log.warning("no custom quota defined for quota scope")
            return QuotaUsage(-1, -1)
        quota_info = custom_defined_quotas[0]
        used_bytes = quota_info.blockUsage * 1024 if quota_info.blockUsage is not None else -1
        limit_bytes = quota_info.blockLimit * 1024 if quota_info.blockLimit is not None else -1
        if used_bytes < 0 or limit_bytes < 0:
            log.warning(
                "negative quota usage reported",
                used_bytes=used_bytes,
                limit_bytes=limit_bytes,
                response_body=quota_info.model_dump_json(),
            )
        return QuotaUsage(
            used_bytes=used_bytes,
            limit_bytes=limit_bytes,
        )

    @override
    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        await self.api_client.remove_quota(self.fs, self._get_fileset_name(quota_scope_id))

    @override
    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        await self.api_client.remove_fileset(self.fs, self._get_fileset_name(quota_scope_id))


class GPFSOpModel(BaseFSOpModel):
    api_client: GPFSAPIClient
    fs: str

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

    @override
    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        await self.api_client.copy_folder(
            self.fs,
            src_path,
            GPFSCopyFolderRequest(
                targetFilesystem=self.fs,
                targetPath=dst_path.as_posix(),
            ),
        )


class GPFSVolume(BaseVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("gpfs")
    api_client: GPFSAPIClient
    fs: str
    gpfs_owner: str

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        watcher: WatcherClient | None = None,
        options: Mapping[str, Any] | None = None,
        volume_name: StorageVolumeName,
        status_check_config: VolumeStatusCheckConfig | None,
    ) -> None:
        super().__init__(
            local_config,
            mount_path,
            etcd=etcd,
            options=options,
            volume_name=volume_name,
            status_check_config=status_check_config,
            event_dispatcher=event_dispatcher,
            event_producer=event_producer,
            watcher=watcher,
        )
        self.api_client = GPFSAPIClient(
            GPFSAPIClientArgs(
                endpoint=self.config["gpfs_endpoint"],
                username=self.config["gpfs_username"],
                password=self.config["gpfs_password"],
                ssl=self.config.get("gpfs_verify_ssl", False),
            )
        )
        self.fs = self.config["gpfs_fs_name"]
        self.gpfs_owner = self.config.get("gpfs_owner", "1000:1000")

    @override
    async def shutdown(self) -> None:
        await self.api_client.aclose()

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        return GPFSQuotaModel(
            self.mount_path,
            self.api_client,
            self.fs,
            self.gpfs_owner,
            fileset_prefix=self.config.get("gpfs_fileset_prefix"),
        )

    @override
    async def create_fsop_model(self) -> AbstractFSOpModel:
        return GPFSOpModel(
            self.mount_path,
            self.local_config["storage-proxy"]["scandir-limit"],
            self.api_client,
            self.fs,
        )

    @override
    async def get_capabilities(self) -> frozenset[StorageBackendCapability]:
        return frozenset([
            StorageBackendCapability.FAST_FS_SIZE,
            StorageBackendCapability.VFOLDER,
            StorageBackendCapability.QUOTA,
            StorageBackendCapability.METRIC,
        ])

    @override
    async def get_hwinfo(self) -> HardwareMetadata:
        nodes = await self.api_client.list_nodes()
        health_state: str | None = None

        for node in nodes:
            if health_state == "ERROR":
                break
            for node_health in await self.api_client.get_node_health(node.adminNodeName):
                if node_health.state in _UNHEALTHY_STATES:
                    health_state = node_health.state

        status: Literal["healthy", "degraded", "unavailable"]
        match health_state:
            case None:
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
                "quota": dump_json_str([q.model_dump(mode="json") for q in quotas]),
                "cluster_info": dump_json_str(cluster_info.model_dump(mode="json")),
            },
        }

    @override
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

    @override
    async def get_performance_metric(self) -> FSPerfMetric:
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
        metrics = await self.api_client.get_metric(query)
        if metrics.performanceData is None or not metrics.performanceData.rows:
            raise GPFSNoMetricError
        latest_metric = metrics.performanceData.rows[-1].values
        if len(latest_metric) < 6:
            raise GPFSNoMetricError
        return FSPerfMetric(
            iops_read=int(latest_metric[0] or 0),
            iops_write=int(latest_metric[1] or 0),
            io_bytes_read=int(latest_metric[2] or 0),
            io_bytes_write=int(latest_metric[3] or 0),
            io_usec_read=latest_metric[4] or 0,
            io_usec_write=latest_metric[5] or 0,
        )
