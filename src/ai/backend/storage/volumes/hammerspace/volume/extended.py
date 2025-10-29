from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Mapping,
    Optional,
    override,
)

from yarl import URL

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.events.event_types.volume.broadcast import DoVolumeMountEvent
from ai.backend.common.types import QuotaConfig, QuotaScopeID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.watcher import WatcherClient

from ....types import CapacityUsage, QuotaUsage
from ...abc import (
    CAP_QUOTA,
    CAP_VFOLDER,
    AbstractQuotaModel,
)
from ...vfs import BaseQuotaModel
from ..client import HammerspaceAPIClient
from ..exception import (
    AuthenticationError,
    ConfigurationError,
)
from ..request import ClusterMetricParams, CreateShareParams, GetShareParams
from ..schema.metric import ValidClusterMetricRow
from ..schema.share import Share, SimpleShare
from ..types import APIConnectionInfo, SSLConfig
from .base import BaseHammerspaceVolume

METRIC_PRECEDING_DURATION = "1h"
METRIC_INTERVAL_DURATION = "5m"


log = BraceStyleAdapter(logging.getLogger(__name__))


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

    def __init__(
        self,
        base_args: HammerspaceQuotaModelBaseArgs,
        client: HammerspaceAPIClient,
    ) -> None:
        super().__init__(mount_path=base_args.mount_target_path)
        self._client = client
        self._event_producer = base_args.event_producer
        self._mount_source = base_args.mount_source
        # `_mount_target_path` is not used becase:
        # Agents has `mount_path` config which is the base path for all mounts
        self._mount_target_path = base_args.mount_target_path

        self._share_query_retry = base_args.share_query_retry
        self._share_query_wait_sec = base_args.share_query_wait_sec

    def _get_share_name(self, quota_scope_id: QuotaScopeID) -> str:
        # Not allowed to name Share with the following characters:
        # \"/\\[]:|<>+;,?*=
        return quota_scope_id.pathname

    def _get_share_path(self, quota_scope_id: QuotaScopeID) -> Path:
        return Path("/", quota_scope_id.pathname)

    def _get_mount_source(self, share: Share | SimpleShare) -> str:
        return f"{self._mount_source}:{share.path}"

    @override
    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        name = self._get_share_name(quota_scope_id)
        path = self._get_share_path(quota_scope_id)
        share_size_limit = options.limit_bytes if options is not None else None

        share = await self._client.create_share(
            CreateShareParams(
                name=name,
                path=path,
                share_size_limit=share_size_limit,
                create_path=True,
                validate_only=False,
            ),
            retry=self._share_query_retry,
            wait_sec=self._share_query_wait_sec,
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
    ) -> Optional[QuotaUsage]:
        name = self._get_share_name(quota_scope_id)
        share = await self._client.get_share(
            GetShareParams(name=name),
        )
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
        # Hammerspace does not support updating shares.
        # TODO: Raise not implemented error and handle it in Manager
        pass

    @override
    async def delete_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
    ) -> None:
        pass


class HammerspaceVolume(BaseHammerspaceVolume):
    name: ClassVar[str] = "hammerspace"

    def __init__(
        self,
        local_config: Mapping[str, Any],
        mount_path: Path,
        *,
        etcd: AsyncEtcd,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        watcher: Optional[WatcherClient] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.local_config = local_config
        self.mount_path = mount_path
        self.config = options or {}
        self.etcd = etcd
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.watcher = watcher

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
        ssl_config: Optional[SSLConfig] = None
        if raw_ssl_config is not None:
            ssl_config = SSLConfig.model_validate(raw_ssl_config)
        self._connection_info = APIConnectionInfo(
            address=URL(address),
            username=username,
            password=password,
            ssl_enabled=ssl_enabled,
            ssl_config=ssl_config,
        )

    @override
    async def init(self) -> None:
        self._client = HammerspaceAPIClient(self._connection_info)
        try:
            await self._client.try_login()
        except AuthenticationError as e:
            raise ConfigurationError(
                "Failed to authenticate to Hammerspace. "
                f"Please check your user account. (username: {self._client._connection_info.username})"
            ) from e

        await super().init()

    @override
    async def create_quota_model(self) -> AbstractQuotaModel:
        base_args = HammerspaceQuotaModelBaseArgs(
            event_producer=self.event_producer,
            mount_source=self._mount_source,
            mount_target_path=self.mount_path,
            share_query_retry=self._share_query_retry,
            share_query_wait_sec=self._share_query_wait_sec,
        )
        quota_model = HammerspaceQuotaModel(
            base_args,
            self._client,
        )
        return quota_model

    @override
    async def get_capabilities(self) -> frozenset[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA])

    async def _get_site_id(self) -> Optional[uuid.UUID]:
        sites = await self._client.get_sites()
        if not sites:
            return None
        site = sites[0]
        return site.uoid.uuid

    async def _get_site_metric_series_row(
        self, site_id: uuid.UUID
    ) -> Optional[ValidClusterMetricRow]:
        metrics = await self._client.get_cluster_metrics(
            params=ClusterMetricParams(
                site_id=site_id,
                preceding_duration=METRIC_PRECEDING_DURATION,
                interval_duration=METRIC_INTERVAL_DURATION,
            )
        )
        if not metrics.series:
            return None

        metric_series = metrics.series[0]
        if not metric_series.rows:
            return None

        sorted_rows = sorted(metric_series.rows, key=lambda r: r.time, reverse=True)
        for row in sorted_rows:
            if (valid_row := row.parse()) is not None:
                return valid_row
        return None

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        site_id = await self._get_site_id()
        if site_id is None:
            log.warning("No sites found in the Hammerspace cluster")
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

        log.warning("No valid metric series rows found in the site (id:{})", site_id)
        return CapacityUsage(
            capacity_bytes=-1,
            used_bytes=-1,
        )
