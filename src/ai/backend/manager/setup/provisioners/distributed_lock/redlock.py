from dataclasses import dataclass
from typing import override

from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_STREAM_LOCK, RedisRole
from ai.backend.common.lock import RedisLock
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import RedisProfileTarget
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class RedLockSpec:
    redis_profile_target: RedisProfileTarget
    lock_retry_interval: float


class RedLockProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "redlock-provisioner"

    @override
    async def setup(self, spec: RedLockSpec) -> DistributedLockFactory:
        redis_lock = redis_helper.get_redis_object(
            spec.redis_profile_target.profile_target(RedisRole.STREAM_LOCK),
            name="lock",
            db=REDIS_STREAM_LOCK,
        )

        return lambda lock_id, lifetime_hint: RedisLock(
            str(lock_id),
            redis_lock,
            lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
            lock_retry_interval=spec.lock_retry_interval,
        )

    @override
    async def teardown(self, resource: DistributedLockFactory) -> None:
        # Nothing to clean up
        pass


class RedLockSpecGenerator(SpecGenerator[RedLockSpec]):
    def __init__(self, redis_stage: ProvisionStage, config: ManagerUnifiedConfig):
        self.redis_stage = redis_stage
        self.config = config

    @override
    async def wait_for_spec(self) -> RedLockSpec:
        redis_clients = await self.redis_stage.wait_for_resource()
        return RedLockSpec(
            redis_profile_target=redis_clients.redis_profile_target,
            lock_retry_interval=0.1,  # Default retry interval
        )
