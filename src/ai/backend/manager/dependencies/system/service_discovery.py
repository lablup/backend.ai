from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.defs import RedisRole
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
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
from ai.backend.common.types import ServiceDiscoveryType, ValkeyProfileTarget
from ai.backend.manager import __version__
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class ServiceDiscoveryInput:
    """Input required for service discovery setup."""

    config: ManagerUnifiedConfig
    etcd: AsyncEtcd
    valkey_profile_target: ValkeyProfileTarget


@dataclass
class ServiceDiscoveryResources:
    """Container for service discovery resources."""

    service_discovery: ServiceDiscovery
    sd_loop: ServiceDiscoveryLoop


class ServiceDiscoveryDependency(
    NonMonitorableDependencyProvider[ServiceDiscoveryInput, ServiceDiscoveryResources],
):
    """Provides ServiceDiscovery and ServiceDiscoveryLoop."""

    @property
    def stage_name(self) -> str:
        return "service-discovery"

    @asynccontextmanager
    async def provide(
        self, setup_input: ServiceDiscoveryInput
    ) -> AsyncIterator[ServiceDiscoveryResources]:
        config = setup_input.config
        sd_type = config.service_discovery.type

        sd: ServiceDiscovery
        match sd_type:
            case ServiceDiscoveryType.ETCD:
                sd = ETCDServiceDiscovery(ETCDServiceDiscoveryArgs(setup_input.etcd))
            case ServiceDiscoveryType.REDIS:
                live_valkey_target = setup_input.valkey_profile_target.profile_target(
                    RedisRole.LIVE
                )
                sd = await RedisServiceDiscovery.create(
                    RedisServiceDiscoveryArgs(valkey_target=live_valkey_target)
                )

        sd_loop = ServiceDiscoveryLoop(
            sd_type,
            sd,
            ServiceMetadata(
                display_name=f"manager-{config.manager.id}",
                service_group="manager",
                version=__version__,
                endpoint=ServiceEndpoint(
                    address=config.manager.announce_addr.address,
                    port=config.manager.announce_addr.port,
                    protocol="http",
                    prometheus_address=config.manager.announce_internal_addr.address,
                ),
            ),
        )

        try:
            yield ServiceDiscoveryResources(
                service_discovery=sd,
                sd_loop=sd_loop,
            )
        finally:
            sd_loop.close()
