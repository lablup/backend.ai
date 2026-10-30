from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar, Literal, override

import aiofiles.os

from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.clients.storage_backends.weka.client import (
    WekaAPIClient,
    WekaAPIClientArgs,
)
from ai.backend.common.clients.storage_backends.weka.exceptions import (
    WekaAPIError,
    WekaInitError,
    WekaNoMetricError,
    WekaNotFoundError,
)
from ai.backend.common.configs.volume_status_check import VolumeStatusCheckConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.common.dto.clients.storage_backends.weka.request import (
    WekaSetQuotaV1Params,
    WekaSetQuotaV1Request,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import HardwareMetadata, QuotaConfig, QuotaScopeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.errors import VolumeNotInitializedError
from ai.backend.storage.types import CapacityUsage, FSPerfMetric, QuotaUsage
from ai.backend.storage.volumes.abc import (
    AbstractQuotaModel,
)
from ai.backend.storage.volumes.vfs import BaseQuotaModel, BaseVolume
from ai.backend.storage.watcher import WatcherClient

log = StructuredLogger(logging.getLogger(__spec__.name))


class WekaQuotaModel(BaseQuotaModel):
    fs_uid: str
    api_client: WekaAPIClient

    def __init__(
        self,
        mount_path: Path,
        fs_uid: str,
        api_client: WekaAPIClient,
    ) -> None:
        super().__init__(mount_path)
        self.fs_uid = fs_uid
        self.api_client = api_client

    async def _ensure_login(self) -> None:
        if not self.api_client.is_logged_in:
            await self.api_client.login()

    async def _get_inode_id(self, path: Path) -> int:
        return await run_in_executor_with_context(
            None,
            lambda: path.stat().st_ino,
        )

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        await aiofiles.os.makedirs(qspath)
        if options is not None:
            await self.update_quota_scope(quota_scope_id, options)

    @override
    async def update_quota_scope(self, quota_scope_id: QuotaScopeID, config: QuotaConfig) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        inode_id = await self._get_inode_id(qspath)
        qs_relpath = qspath.relative_to(self.mount_path).as_posix()
        if not qs_relpath.startswith("/"):
            qs_relpath = "/" + qs_relpath
        await self._ensure_login()
        await self.api_client.set_quota_v1(
            WekaSetQuotaV1Request(
                params=WekaSetQuotaV1Params(
                    inode_context=inode_id,
                    path=qs_relpath,
                    soft_limit_bytes=config.limit_bytes,
                    hard_limit_bytes=config.limit_bytes,
                )
            )
        )

    @override
    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> QuotaUsage | None:
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            return None

        inode_id = await self._get_inode_id(qspath)
        await self._ensure_login()
        quota = await self.api_client.get_quota(self.fs_uid, inode_id)
        used_bytes = quota.used_bytes if quota.used_bytes is not None else -1
        limit_bytes = quota.hard_limit if quota.hard_limit is not None else -1
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
    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        qspath = self.mangle_qspath(quota_scope_id)
        inode_id = await self._get_inode_id(qspath)
        await self._ensure_login()
        try:
            await self.api_client.remove_quota(self.fs_uid, inode_id)
        except WekaNotFoundError:
            pass

    @override
    async def delete_quota_scope(self, quota_scope_id: QuotaScopeID) -> None:
        await self.unset_quota(quota_scope_id)
        await aiofiles.os.rmdir(self.mangle_qspath(quota_scope_id))


class WekaVolume(BaseVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("weka")
    api_client: WekaAPIClient
    _fs_uid: str | None

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
        self.api_client = WekaAPIClient(
            WekaAPIClientArgs(
                endpoint=self.config["weka_endpoint"],
                username=self.config["weka_username"],
                password=self.config["weka_password"],
                organization=self.config["weka_organization"],
                ssl_context=self.config.get("weka_verify_ssl", False),
            )
        )
        self._fs_uid = None

    async def _ensure_login(self) -> None:
        if not self.api_client.is_logged_in:
            await self.api_client.login()

    def _get_fs_uid(self) -> str:
        if self._fs_uid is None:
            raise VolumeNotInitializedError("Weka filesystem UID is not initialized")
        return self._fs_uid

    @override
    async def init(self) -> None:
        await self._ensure_login()
        for fs in await self.api_client.list_fs():
            if fs.name == self.config["weka_fs_name"]:
                self._fs_uid = fs.uid
                break
        else:
            raise WekaInitError(f"FileSystem {self.config['weka_fs_name']} not found")
        await super().init()

    @override
    async def shutdown(self) -> None:
        await self.api_client.aclose()

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        return WekaQuotaModel(self.mount_path, self._get_fs_uid(), self.api_client)

    @override
    async def get_capabilities(self) -> frozenset[StorageBackendCapability]:
        return frozenset([
            StorageBackendCapability.VFOLDER,
            StorageBackendCapability.QUOTA,
            StorageBackendCapability.METRIC,
            StorageBackendCapability.FAST_FS_SIZE,
        ])

    @override
    async def get_hwinfo(self) -> HardwareMetadata:
        fs_uid = self._get_fs_uid()
        await self._ensure_login()
        raw_status = (await self.api_client.check_health()).status.lower()
        status: Literal["healthy", "degraded", "offline", "unavailable"]
        match raw_status:
            case "ok" | "healthy":
                status = "healthy"
            case "degraded":
                status = "degraded"
            case "offline":
                status = "offline"
            case _:
                status = "unavailable"
        try:
            cluster_info = await self.api_client.get_cluster_info()
            quotas = await self.api_client.list_quotas(fs_uid)
            return {
                "status": status,
                "status_info": raw_status,
                "metadata": {
                    "quota": dump_json_str([q.model_dump(mode="json") for q in quotas]),
                    "cluster_info": dump_json_str(cluster_info.model_dump(mode="json")),
                },
            }
        except WekaAPIError:
            return {
                "status": status,
                "status_info": raw_status,
                "metadata": {},
            }

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        fs_uid = self._get_fs_uid()
        await self._ensure_login()
        fs = await self.api_client.get_fs(fs_uid)
        return CapacityUsage(
            capacity_bytes=fs.total_budget,
            used_bytes=fs.used_total,
        )

    @override
    async def get_performance_metric(self) -> FSPerfMetric:
        start_time = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(
            minutes=1,
        )
        await self._ensure_login()
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
        try:
            latest_metric = metrics.categories["ops"][-1].stats
            return FSPerfMetric(
                iops_read=int(latest_metric["READS"] or 0),
                iops_write=int(latest_metric["WRITES"] or 0),
                io_bytes_read=int(latest_metric["READ_BYTES"] or 0),
                io_bytes_write=int(latest_metric["WRITE_BYTES"] or 0),
                io_usec_read=latest_metric["READ_LATENCY"] or 0,
                io_usec_write=latest_metric["WRITE_LATENCY"] or 0,
            )
        except (KeyError, IndexError) as e:
            raise WekaNoMetricError from e
