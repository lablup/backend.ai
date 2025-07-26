from dataclasses import dataclass
from typing import override

from ai.backend.common.defs import RedisRole
from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
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


class RedisServiceDiscoverySpecGenerator(SpecGenerator[RedisServiceDiscoverySpec]):
    def __init__(self, redis_stage: ProvisionStage):
        self.redis_stage = redis_stage

    @override
    async def wait_for_spec(self) -> RedisServiceDiscoverySpec:
        redis_clients = await self.redis_stage.wait_for_resource()
        # Use the live Redis target for service discovery
        redis_target = redis_clients.redis_profile_target.profile_target(RedisRole.LIVE)
        return RedisServiceDiscoverySpec(redis_target=redis_target)
