from dataclasses import dataclass
from typing import override

from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import RedisTarget


@dataclass
class RedisServiceDiscoverySpec:
    redis_target: RedisTarget


class RedisServiceDiscoveryProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "redis-service-discovery-provisioner"

    @override
    async def setup(self, spec: RedisServiceDiscoverySpec) -> RedisServiceDiscovery:
        return await RedisServiceDiscovery.create(
            RedisServiceDiscoveryArgs(redis_target=spec.redis_target)
        )

    @override
    async def teardown(self, resource: RedisServiceDiscovery) -> None:
        # Nothing to clean up
        pass
