from __future__ import annotations

import pytest

from ai.backend.agent.dependencies.infrastructure.redis import AgentValkeyDependency
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.typed_validators import HostPortPair


class TestValkeyDependency:
    @pytest.fixture
    async def redis_config(self, redis_container) -> RedisConfig:
        """Redis config fixture using testcontainer."""
        redis_addr = redis_container[1]
        return RedisConfig(
            addr=HostPortPair(host=redis_addr.host, port=redis_addr.port),
            password=None,
        )

    @pytest.mark.asyncio
    async def test_valkey_dependency_creates_all_clients(self, redis_config: RedisConfig) -> None:
        """Test that valkey dependency creates all 4 clients."""
        dependency = AgentValkeyDependency()

        async with dependency.provide(redis_config) as clients:
            # Verify all 4 clients are created
            assert clients.stat is not None
            assert clients.stream is not None
            assert clients.bgtask is not None
            assert clients.container_log is not None
