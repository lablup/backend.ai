from __future__ import annotations

from unittest.mock import Mock

import pytest

from ai.backend.appproxy.worker.config import ServerConfig
from ai.backend.appproxy.worker.dependencies.infrastructure.redis import (
    RedisProvider,
    WorkerValkeyClients,
)
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestRedisProvider:
    """Test RedisProvider with real Redis container."""

    @pytest.fixture
    def worker_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> ServerConfig:
        """Create a worker config pointing to the test redis container."""
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

        # Create minimal configs with Mock

        config = Mock(spec=ServerConfig)
        # redis_config is already a dict, wrap it in Mock with to_dict method
        redis_mock = Mock()
        redis_mock.to_dict.return_value = redis_config
        config.redis = redis_mock
        return config

    @pytest.mark.asyncio
    async def test_provide_valkey_clients(
        self,
        worker_config: ServerConfig,
    ) -> None:
        """Dependency should create and cleanup all Valkey clients."""
        dependency = RedisProvider()

        async with dependency.provide(worker_config) as clients:
            assert isinstance(clients, WorkerValkeyClients)
            # Verify clients are functional
            assert clients.valkey_live is not None
            assert clients.valkey_stat is not None

            # Test basic operation on live client
            server_time = await clients.valkey_live.get_server_time()
            assert server_time > 0

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        worker_config: ServerConfig,
    ) -> None:
        """Dependency should cleanup clients even on exception."""
        dependency = RedisProvider()

        with pytest.raises(RuntimeError):
            async with dependency.provide(worker_config) as clients:
                assert isinstance(clients, WorkerValkeyClients)
                raise RuntimeError("Test error")

        # Clients should be closed - we can't easily verify this,
        # but the test should complete without hanging
