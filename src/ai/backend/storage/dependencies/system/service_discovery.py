from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import RedisRole
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.event_publisher import ServiceDiscoveryEventPublisher
from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.types import HostPortPair, ServiceDiscoveryType
from ai.backend.storage import __version__
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig


@dataclass
class ServiceDiscoveryInput:
    """Input required for service discovery setup."""

    local_config: StorageProxyUnifiedConfig
    etcd: AsyncEtcd
    redis_config: RedisConfig
    event_producer: EventProducer


@dataclass
class ServiceDiscoveryResources:
    """Container for service discovery resources."""

    service_discovery: ServiceDiscovery
    sd_loop: ServiceDiscoveryLoop


class ServiceDiscoveryProvider(
    NonMonitorableDependencyProvider[ServiceDiscoveryInput, ServiceDiscoveryResources]
):
    """Provides ServiceDiscovery, its announcement loop and the event publisher."""

    @property
    @override
    def stage_name(self) -> str:
        return "service-discovery"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: ServiceDiscoveryInput
    ) -> AsyncIterator[ServiceDiscoveryResources]:
        local_config = setup_input.local_config
        sd_config = local_config.service_discovery
        sd_type = sd_config.type

        service_discovery: ServiceDiscovery
        match sd_type:
            case ServiceDiscoveryType.ETCD:
                service_discovery = ETCDServiceDiscovery(ETCDServiceDiscoveryArgs(setup_input.etcd))
            case ServiceDiscoveryType.REDIS:
                valkey_profile_target = setup_input.redis_config.to_valkey_profile_target()
                service_discovery = await RedisServiceDiscovery.create(
                    args=RedisServiceDiscoveryArgs(
                        valkey_target=valkey_profile_target.profile_target(RedisRole.LIVE)
                    )
                )

        announce_addr_config = local_config.api.manager.announce_addr
        announce_addr = HostPortPair(
            host=announce_addr_config.host,
            port=announce_addr_config.port,
        )
        announce_internal_addr_config = local_config.api.manager.announce_internal_addr
        announce_internal_addr = HostPortPair(
            host=announce_internal_addr_config.host,
            port=announce_internal_addr_config.port,
        )
        sd_loop = ServiceDiscoveryLoop(
            sd_type,
            service_discovery,
            ServiceMetadata(
                display_name=f"storage-{local_config.storage_proxy.node_id}",
                service_group="storage-proxy",
                version=__version__,
                endpoint=ServiceEndpoint(
                    address=str(announce_addr),
                    port=announce_addr.port,
                    protocol="http",
                    prometheus_address=str(announce_internal_addr),
                ),
            ),
        )

        sd_event_publisher: ServiceDiscoveryEventPublisher | None = None
        if sd_config.service_group:
            sd_event_publisher = ServiceDiscoveryEventPublisher(
                event_producer=setup_input.event_producer,
                config=sd_config,
                component_version=__version__,
                startup_time=datetime.now(tz=UTC),
            )
            await sd_event_publisher.start()

        try:
            yield ServiceDiscoveryResources(
                service_discovery=service_discovery,
                sd_loop=sd_loop,
            )
        finally:
            if sd_event_publisher is not None:
                await sd_event_publisher.stop()
            sd_loop.close()
