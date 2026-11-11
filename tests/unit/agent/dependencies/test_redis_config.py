from __future__ import annotations

from unittest.mock import MagicMock

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.dependencies.bootstrap.redis_config import RedisConfigDependency
from ai.backend.common.configs.redis import RedisConfig


class TestRedisConfigDependency:
    async def test_provides_redis_config_from_local_config(self) -> None:
        local_redis = RedisConfig.model_validate({
            "addr": "192.168.1.100:6380",
            "password": "local-password",
        })
        config = MagicMock(spec=AgentUnifiedConfig)
        config.redis = local_redis

        async with RedisConfigDependency().provide(config) as redis_config:
            assert redis_config is local_redis
