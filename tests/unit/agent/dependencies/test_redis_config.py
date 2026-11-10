from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.dependencies.bootstrap.redis_config import RedisConfigDependency
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.exception import ConfigurationError


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

    async def test_raises_when_redis_config_is_missing(self) -> None:
        config = MagicMock(spec=AgentUnifiedConfig)
        config.redis = None

        with pytest.raises(ConfigurationError):
            async with RedisConfigDependency().provide(config):
                pass
