from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)


@dataclass
class RedisConfigSpec:
    etcd: AsyncEtcd


class RedisConfigSpecGenerator(ArgsSpecGenerator[RedisConfigSpec]):
    pass


@dataclass
class RedisConfigResult:
    redis_config: RedisConfig


class RedisConfigProvisioner(Provisioner[RedisConfigSpec, RedisConfigResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-redis-config"

    @override
    async def setup(self, spec: RedisConfigSpec) -> RedisConfigResult:
        raw_redis_config = await spec.etcd.get_prefix("config/redis")
        redis_config = RedisConfig.model_validate(raw_redis_config)
        return RedisConfigResult(redis_config)

    @override
    async def teardown(self, resource: RedisConfigResult) -> None:
        pass


class RedisConfigStage(ProvisionStage[RedisConfigSpec, RedisConfigResult]):
    pass
