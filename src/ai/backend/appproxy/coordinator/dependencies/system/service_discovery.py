from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.appproxy.coordinator import __version__
from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.errors.config import UnsupportedServiceDiscoveryTypeError
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.defs import RedisRole
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
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
from ai.backend.common.types import RedisProfileTarget, ServiceDiscoveryType


@dataclass
class ServiceDiscoveryInput:
    config: ServerConfig
    sentinel_monitors: SentinelMonitorSet


@dataclass
class ServiceDiscoveryResources:
    worker_service_discovery: ServiceDiscovery
    core_service_discovery: ServiceDiscovery
    sd_loop: ServiceDiscoveryLoop


class ServiceDiscoveryProvider(
    NonMonitorableDependencyProvider[ServiceDiscoveryInput, ServiceDiscoveryResources],
):
    """Discovers the AppProxy workers and announces the coordinator to the core."""

    @property
    @override
    def stage_name(self) -> str:
        return "service-discovery"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: ServiceDiscoveryInput
    ) -> AsyncIterator[ServiceDiscoveryResources]:
        config = setup_input.config
        sentinel_monitors = setup_input.sentinel_monitors
        sd_type = config.service_discovery.type
        core_service_discovery: ServiceDiscovery
        worker_service_discovery: ServiceDiscovery
        match sd_type:
            case ServiceDiscoveryType.REDIS:
                # Workers register in the AppProxy redis, which core redis may not be.
                worker_live_target = (
                    RedisProfileTarget.from_dict(config.redis.to_dict())
                    .profile_target(RedisRole.LIVE)
                    .to_valkey_target()
                )
                worker_service_discovery = await RedisServiceDiscovery.create(
                    RedisServiceDiscoveryArgs(
                        valkey_target=worker_live_target,
                        sentinel_monitor=sentinel_monitors.monitor_for(worker_live_target),
                    )
                )
                if config.core_redis is None:
                    core_service_discovery = worker_service_discovery
                else:
                    core_live_target = (
                        RedisProfileTarget.from_dict(config.core_redis.to_dict())
                        .profile_target(RedisRole.LIVE)
                        .to_valkey_target()
                    )
                    core_service_discovery = await RedisServiceDiscovery.create(
                        RedisServiceDiscoveryArgs(
                            valkey_target=core_live_target,
                            sentinel_monitor=sentinel_monitors.monitor_for(core_live_target),
                        )
                    )
            case _:
                raise UnsupportedServiceDiscoveryTypeError(
                    f"Unsupported service discovery type: {sd_type}. "
                    "Please use Redis service discovery for appproxy."
                )

        announce_addr = config.proxy_coordinator.announce_addr
        sd_loop = ServiceDiscoveryLoop(
            sd_type,
            core_service_discovery,
            ServiceMetadata.for_endpoint(
                display_name=f"appproxy-coordinator-{config.proxy_coordinator.id}",
                service_group="appproxy-coordinator",
                version=__version__,
                endpoint=ServiceEndpoint(
                    address=announce_addr.host,
                    port=announce_addr.port,
                    protocol="http",
                    # It can be separated into an internal-purpose port later.
                    prometheus_address=str(announce_addr),
                ),
            ),
        )
        try:
            yield ServiceDiscoveryResources(
                worker_service_discovery=worker_service_discovery,
                core_service_discovery=core_service_discovery,
                sd_loop=sd_loop,
            )
        finally:
            sd_loop.close()
            # sd_loop unregisters after close() returns, so the discovery it uses stays open.
            if config.core_redis is not None:
                await worker_service_discovery.close()
