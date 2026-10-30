from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, cast, override

import aiofiles.os

from ai.backend.common.clients.storage_backends.dellemc.client import OneFSClient, OneFSClientArgs
from ai.backend.common.configs.volume_status_check import VolumeStatusCheckConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.common.dto.clients.storage_backends.dellemc.request import (
    OneFSCreateQuotaRequest,
    OneFSUpdateQuotaRequest,
)
from ai.backend.common.dto.clients.storage_backends.dellemc.response import OneFSQuotaThresholds
from ai.backend.common.dto.clients.storage_backends.dellemc.types import (
    OneFSQuotaID,
    OneFSQuotaType,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import HardwareMetadata, QuotaScopeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.errors import QuotaDirectoryNotEmptyError
from ai.backend.storage.types import CapacityUsage, FSPerfMetric, QuotaConfig, QuotaUsage
from ai.backend.storage.volumes.abc import (
    AbstractQuotaModel,
)
from ai.backend.storage.volumes.vfs import BaseQuotaModel, BaseVolume
from ai.backend.storage.watcher import WatcherClient

from .config import config_iv

log = StructuredLogger(logging.getLogger(__spec__.name))


class DellEMCOneFSQuotaModel(BaseQuotaModel):
    ifs_path: Path
    api_client: OneFSClient

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

    async def _set_quota_id(self, qspath: Path, quota_id: OneFSQuotaID) -> None:
        quota_id_path = qspath / ".quota_id"
        async with aiofiles.open(quota_id_path, "w") as file:
            await file.write(quota_id.rstrip())

    async def _get_quota_id(self, qspath: Path) -> OneFSQuotaID | None:
        """
        Read OneFS quota id of the given path.
        Return `None` if no quota is set to the path.
        """
        quota_id_path = qspath / ".quota_id"
        if quota_id_path.exists():
            async with aiofiles.open(quota_id_path) as file:
                quota_id = await file.read()
            return OneFSQuotaID(quota_id.rstrip())
        return None

    async def _unset_quota_id(self, qspath: Path) -> None:
        quota_id_path = qspath / ".quota_id"
        if quota_id_path.exists():
            await aiofiles.os.remove(quota_id_path)

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.makedirs(qspath, exist_ok=True)
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    @override
    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> QuotaUsage | None:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id = await self._get_quota_id(qspath)
        if quota_id is None:
            return None
        quota = await self.api_client.get_quota(quota_id)
        used_bytes = quota.usage.fslogical if quota.usage.fslogical is not None else -1
        limit_bytes = quota.thresholds.hard if quota.thresholds.hard is not None else -1
        if used_bytes < 0 or limit_bytes < 0:
            log.warning(
                "negative quota usage reported",
                used_bytes=used_bytes,
                limit_bytes=limit_bytes,
                response_body=quota.model_dump_json(),
            )
        return QuotaUsage(
            used_bytes=used_bytes,
            limit_bytes=limit_bytes,
        )

    @override
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id = await self._get_quota_id(qspath)
        thresholds = OneFSQuotaThresholds(hard=config.limit_bytes)
        if quota_id is not None:
            await self.api_client.update_quota(
                quota_id,
                OneFSUpdateQuotaRequest(thresholds=thresholds),
            )
        else:
            quota_target_path = self.ifs_path / quota_scope_id.pathname
            result = await self.api_client.create_quota(
                OneFSCreateQuotaRequest(
                    path=str(quota_target_path),
                    type=OneFSQuotaType.DIRECTORY,
                    thresholds=thresholds,
                )
            )
            await self._set_quota_id(qspath, result.id)

    @override
    async def unset_quota(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        quota_id = await self._get_quota_id(qspath)
        if len([p for p in qspath.iterdir() if p.is_dir()]) > 0:
            raise QuotaDirectoryNotEmptyError(
                f"Cannot delete quota scope '{quota_scope_id}': directory not empty"
            )
        if quota_id is not None:
            await self.api_client.delete_quota(quota_id)
            await self._unset_quota_id(qspath)

    @override
    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        await self.unset_quota(quota_scope_id)
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.rmdir(qspath)


class DellEMCOneFSVolume(BaseVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("dellemc-onefs")
    api_client: OneFSClient

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
        self.config = cast(Mapping[str, Any], config_iv.check(self.config))
        self.api_client = OneFSClient(
            OneFSClientArgs(
                endpoint=str(self.config["dell_endpoint"]),
                user=self.config["dell_username"],
                password=str(self.config["dell_password"]),
                api_version=self.config["dell_api_version"],
                system_name=self.config["dell_system_name"],
            )
        )

    @override
    async def shutdown(self) -> None:
        await self.api_client.aclose()

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        ifs_path = Path(self.config["dell_ifs_path"])
        return DellEMCOneFSQuotaModel(
            self.mount_path, api_client=self.api_client, ifs_path=ifs_path
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
        metadata = await self.api_client.get_metadata()
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {"cluster": metadata.cluster, "nodes": metadata.nodes},
        }

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        usage = await self.api_client.get_usage()
        return CapacityUsage(
            capacity_bytes=usage.capacity_bytes,
            used_bytes=usage.used_bytes,
        )

    @override
    async def get_performance_metric(self) -> FSPerfMetric:
        protocol_stats = await self.api_client.get_protocol_stats()
        workload = await self.api_client.get_workload_stats()
        disk_iops = protocol_stats.disk.iops if protocol_stats.disk is not None else None
        onefs_out = protocol_stats.onefs.out if protocol_stats.onefs is not None else None
        onefs_in = protocol_stats.onefs.in_ if protocol_stats.onefs is not None else None
        latency_write = workload.latency_write if workload is not None else None
        latency_read = workload.latency_read if workload is not None else None
        return FSPerfMetric(
            iops_read=int(disk_iops or 0),
            iops_write=0,
            io_bytes_read=int(onefs_out or 0),
            io_bytes_write=int(onefs_in or 0),
            io_usec_read=latency_write or 0,
            io_usec_write=latency_read or 0,
        )
