from __future__ import annotations

import pytest

from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.dependencies.infrastructure.redis import (
    CoordinatorValkeyClients,
    RedisProvider,
)
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestRedisProvider:
    """Test RedisProvider with real Redis container."""

    @pytest.fixture
    def coordinator_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> ServerConfig:
        """Create a coordinator config pointing to the test redis container."""
        from ai.backend.common.config import redis_config_iv
        from ai.backend.common.types import HostPortPair

        container_id, redis_addr = redis_container

        # Create Redis config with single endpoint for all roles
        redis_config_data = {
            "addr": HostPortPair(host=redis_addr.host, port=redis_addr.port),
            "sentinel": None,
            "service_name": None,
            "password": None,
        }
        redis_config = redis_config_iv.check(redis_config_data)

        # Create minimal ServerConfig with just redis settings
        config = ServerConfig(redis=redis_config)  # type: ignore[call-arg]
        return config

    @pytest.mark.asyncio
    async def test_provide_valkey_clients(
        self,
        coordinator_config: ServerConfig,
    ) -> None:
        """Dependency should create and cleanup all Valkey clients."""
        dependency = RedisProvider()

        async with dependency.provide(coordinator_config) as clients:
            assert isinstance(clients, CoordinatorValkeyClients)
            # Verify clients are functional
            assert clients.valkey_live is not None
            assert clients.core_valkey_live is not None
            assert clients.redis_lock is not None
            assert clients.valkey_schedule is not None

            # Test basic operation on live client
            server_time = await clients.valkey_live.get_server_time()
            assert server_time > 0

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        coordinator_config: ServerConfig,
    ) -> None:
        """Dependency should cleanup clients even on exception."""
        dependency = RedisProvider()

        with pytest.raises(RuntimeError):
            async with dependency.provide(coordinator_config) as clients:
                assert isinstance(clients, CoordinatorValkeyClients)
                raise RuntimeError("Test error")

        # Clients should be closed - we can't easily verify this,
        # but the test should complete without hanging
