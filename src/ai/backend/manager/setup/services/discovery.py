from __future__ import annotations

from dataclasses import dataclass

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
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import RedisProfileTarget, RedisRole, ServiceDiscoveryType
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager import __version__


@dataclass
class ServiceDiscoverySpec:
    config: ManagerUnifiedConfig
    etcd: AsyncEtcd
    redis_profile_target: RedisProfileTarget


@dataclass
class ServiceDiscoveryResource:
    service_discovery: ETCDServiceDiscovery | RedisServiceDiscovery
    sd_loop: ServiceDiscoveryLoop


class ServiceDiscoveryProvisioner(Provisioner[ServiceDiscoverySpec, ServiceDiscoveryResource]):
    @property
    def name(self) -> str:
        return "service_discovery"

    async def setup(self, spec: ServiceDiscoverySpec) -> ServiceDiscoveryResource:
        sd_type = spec.config.service_discovery.type
        
        match sd_type:
            case ServiceDiscoveryType.ETCD:
                service_discovery = ETCDServiceDiscovery(
                    ETCDServiceDiscoveryArgs(spec.etcd)
                )
            case ServiceDiscoveryType.REDIS:
                live_redis_target = spec.redis_profile_target.profile_target(RedisRole.LIVE)
                service_discovery = await RedisServiceDiscovery.create(
                    RedisServiceDiscoveryArgs(redis_target=live_redis_target)
                )

        sd_loop = ServiceDiscoveryLoop(
            sd_type,
            service_discovery,
            ServiceMetadata(
                display_name=f"manager-{spec.config.manager.id}",
                service_group="manager",
                version=__version__,
                endpoint=ServiceEndpoint(
                    address=spec.config.manager.announce_addr.address,
                    port=spec.config.manager.announce_addr.port,
                    protocol="http",
                    prometheus_address=spec.config.manager.announce_internal_addr.address,
                ),
            ),
        )

        # Note: OTEL configuration is handled separately by the application setup
        
        return ServiceDiscoveryResource(
            service_discovery=service_discovery,
            sd_loop=sd_loop,
        )

    async def teardown(self, resource: ServiceDiscoveryResource) -> None:
        resource.sd_loop.close()