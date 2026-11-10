from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    override,
)

from ai.backend.common.clients.storage_backends.hammerspace.client import (
    HammerspaceAPIClient,
    HammerspaceAPIClientArgs,
)
from ai.backend.common.clients.storage_backends.hammerspace.exceptions import (
    AuthenticationError,
)
from ai.backend.common.configs.volume_status_check import VolumeStatusCheckConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.common.dto.clients.storage_backends.hammerspace.request import (
    HammerspaceCreateShareRequest,
)
from ai.backend.common.dto.clients.storage_backends.hammerspace.response import (
    Share,
    SimpleShare,
    ValidClusterMetricRow,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.events.event_types.volume.broadcast import DoVolumeMountEvent
from ai.backend.common.types import QuotaConfig, QuotaScopeID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.errors import VolumeNotInitializedError
from ai.backend.storage.types import CapacityUsage, QuotaUsage
from ai.backend.storage.volumes.abc import (
    AbstractQuotaModel,
)
from ai.backend.storage.volumes.hammerspace.exception import ConfigurationError
from ai.backend.storage.volumes.hammerspace.types import SSLConfig
from ai.backend.storage.volumes.vfs import BaseQuotaModel
from ai.backend.storage.watcher import WatcherClient

from .base import BaseHammerspaceVolume

METRIC_PRECEDING_DURATION = "1h"
METRIC_INTERVAL_DURATION = "5m"

log = StructuredLogger(logging.getLogger(__name__))


@dataclass
class HammerspaceQuotaModelBaseArgs:
    event_producer: EventProducer
    mount_source: str
    mount_target_path: Path
    share_query_retry: int
    share_query_wait_sec: int


class HammerspaceQuotaModel(BaseQuotaModel):
    _client: HammerspaceAPIClient
    _event_producer: EventProducer
    _mount_source: str
    _mount_target_path: Path
    _share_query_retry: int
    _share_query_wait_sec: int

    def __init__(
        self,
        base_args: HammerspaceQuotaModelBaseArgs,
        client: HammerspaceAPIClient,
    ) -> None:
        super().__init__(mount_path=base_args.mount_target_path)
        self._client = client
        self._event_producer = base_args.event_producer
        self._mount_source = base_args.mount_source
        self._mount_target_path = base_args.mount_target_path

        self._share_query_retry = base_args.share_query_retry
        self._share_query_wait_sec = base_args.share_query_wait_sec

    async def _ensure_login(self) -> None:
        if not self._client.is_logged_in:
            await self._client.login()

    def _get_share_name(self, quota_scope_id: QuotaScopeID) -> str:
        return quota_scope_id.pathname

    def _get_share_path(self, quota_scope_id: QuotaScopeID) -> Path:
        return Path("/", quota_scope_id.pathname)

    def _get_mount_source(self, share: Share | SimpleShare) -> str:
        return f"{self._mount_source}:{share.path}"

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: QuotaConfig | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> None:
        name = self._get_share_name(quota_scope_id)
        path = self._get_share_path(quota_scope_id)
        share_size_limit = options.limit_bytes if options is not None else None

        await self._ensure_login()
        share = await self._client.create_share(
            HammerspaceCreateShareRequest(
                name=name,
                path=str(path),
                shareSizeLimit=share_size_limit,
            ),
            retry=self._share_query_retry,
            wait_sec=self._share_query_wait_sec,
            create_path=True,
            validate_only=False,
        )
        dir_name = str(self.mangle_qspath(quota_scope_id))
        await self._event_producer.broadcast_event(
            DoVolumeMountEvent(
                dir_name=dir_name,
                volume_backend_name="hammerspace",
                fs_location=self._get_mount_source(share),
                quota_scope_id=quota_scope_id,
                edit_fstab=True,
            ),
            None,
        )

    @override
    async def describe_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> QuotaUsage | None:
        name = self._get_share_name(quota_scope_id)
        await self._ensure_login()
        share = await self._client.get_share(name)
        if share is None:
            return None
        return QuotaUsage(
            used_bytes=share.space.used,
            limit_bytes=share.space.total,
        )

    @override
    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        pass

    @override
    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        pass


class HammerspaceVolume(BaseHammerspaceVolume):
    name: ClassVar[StorageBackendType] = StorageBackendType("hammerspace")
    _client: HammerspaceAPIClient | None
    _client_args: HammerspaceAPIClientArgs
    _mount_source: str
    _share_query_retry: int
    _share_query_wait_sec: int

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
        self.local_config = local_config
        self.mount_path = mount_path
        self.config = options or {}
        self.etcd = etcd
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.watcher = watcher
        self._volume_name = volume_name
        self._status_check_config = status_check_config
        self._client = None

        address = self.config.get("address")
        if address is None:
            raise ConfigurationError("Hammerspace volume requires 'address' in options")
        username = self.config.get("username")
        if username is None:
            raise ConfigurationError("Hammerspace volume requires 'username' in options")
        password = self.config.get("password")
        if password is None:
            raise ConfigurationError("Hammerspace volume requires 'password' in options")

        mount_source = self.config.get("mount_source")
        if mount_source is None:
            raise ConfigurationError("Hammerspace volume requires 'mount_source' in options")
        self._mount_source = mount_source

        share_query_retry = self.config.get("share_query_retry", 5)
        share_query_wait_sec = self.config.get("share_query_wait_sec", 1)
        self._share_query_retry = int(share_query_retry)
        self._share_query_wait_sec = int(share_query_wait_sec)

        ssl_enabled = self.config.get("ssl_enabled", False)
        raw_ssl_config = self.config.get("ssl_config", None)
        if raw_ssl_config is not None:
            SSLConfig.model_validate(raw_ssl_config)
        self._client_args = HammerspaceAPIClientArgs(
            address=str(address),
            username=username,
            password=password,
            ssl_enabled=bool(ssl_enabled),
        )

    @property
    def client(self) -> HammerspaceAPIClient:
        if self._client is None:
            raise VolumeNotInitializedError("Hammerspace client is not initialized")
        return self._client

    async def _ensure_login(self) -> None:
        if not self.client.is_logged_in:
            await self.client.login()

    @override
    async def init(self) -> None:
        self._client = HammerspaceAPIClient(self._client_args)
        try:
            await self._client.login()
        except AuthenticationError as e:
            raise ConfigurationError(
                "Failed to authenticate to Hammerspace. "
                f"Please check your user account. (username: {self._client_args.username})"
            ) from e

        await super().init()

    @override
    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        base_args = HammerspaceQuotaModelBaseArgs(
            event_producer=self.event_producer,
            mount_source=self._mount_source,
            mount_target_path=self.mount_path,
            share_query_retry=self._share_query_retry,
            share_query_wait_sec=self._share_query_wait_sec,
        )
        return HammerspaceQuotaModel(
            base_args,
            self.client,
        )

    @override
    async def get_capabilities(self) -> frozenset[StorageBackendCapability]:
        return frozenset([StorageBackendCapability.VFOLDER, StorageBackendCapability.QUOTA])

    async def _get_site_id(self) -> uuid.UUID | None:
        await self._ensure_login()
        sites = await self.client.get_sites()
        if not sites:
            return None
        site = sites[0]
        return site.uoid.uuid

    async def _get_site_metric_series_row(self, site_id: uuid.UUID) -> ValidClusterMetricRow | None:
        await self._ensure_login()
        metrics = await self.client.get_cluster_metrics(
            site_id,
            METRIC_PRECEDING_DURATION,
            METRIC_INTERVAL_DURATION,
        )
        if not metrics.series:
            return None

        metric_series = metrics.series[0]
        if not metric_series.rows:
            return None

        sorted_rows = sorted(metric_series.rows, key=lambda r: r.time, reverse=True)
        for row in sorted_rows:
            if row.total is None or row.used is None or row.free is None:
                continue
            return ValidClusterMetricRow(
                time=row.time, total=row.total, used=row.used, free=row.free
            )
        return None

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        site_id = await self._get_site_id()
        if site_id is None:
            log.warning("no sites found in the Hammerspace cluster")
            return CapacityUsage(
                capacity_bytes=-1,
                used_bytes=-1,
            )

        valid_row = await self._get_site_metric_series_row(site_id)
        if valid_row is not None:
            return CapacityUsage(
                capacity_bytes=valid_row.total,
                used_bytes=valid_row.used,
            )

        log.warning("no valid metric series rows found in site", site_id=str(site_id))
        return CapacityUsage(
            capacity_bytes=-1,
            used_bytes=-1,
        )
