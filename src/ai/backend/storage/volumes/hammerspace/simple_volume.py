from __future__ import annotations

import logging
import uuid
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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.watcher import WatcherClient

from ...types import CapacityUsage
from ..abc import (
    CAP_VFOLDER,
)
from ..vfs import BaseVolume
from .client import HammerspaceAPIClient
from .exception import (
    AuthenticationError,
    ConfigurationError,
)
from .request import ClusterMetricParams
from .schema.metric import ValidClusterMetricRow
from .types import APIConnectionInfo, SSLConfig

METRIC_PRECEDING_DURATION = "1h"
METRIC_INTERVAL_DURATION = "5m"


log = BraceStyleAdapter(logging.getLogger(__name__))


class HammerspaceSimpleVolume(BaseVolume):
    name: ClassVar[str] = "hammerspace-simple"

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
    async def get_capabilities(self) -> frozenset[str]:
        return frozenset([CAP_VFOLDER])

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
