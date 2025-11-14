from __future__ import annotations

import pytest

from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.infrastructure.redis import (
    ValkeyClients,
    ValkeyDependency,
)
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestValkeyDependency:
    """Test ValkeyDependency with real Redis container."""

    @pytest.fixture
    def manager_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> ManagerUnifiedConfig:
        """Create a manager config pointing to the test redis container."""
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

        # Create minimal ManagerUnifiedConfig with just redis settings
        config = ManagerUnifiedConfig(redis=redis_config)  # type: ignore[call-arg]
        return config

    @pytest.mark.asyncio
    async def test_provide_valkey_clients(
        self,
        manager_config: ManagerUnifiedConfig,
    ) -> None:
        """Dependency should create and cleanup all Valkey clients."""
        dependency = ValkeyDependency()

        async with dependency.provide(manager_config) as clients:
            assert isinstance(clients, ValkeyClients)
            # Verify clients are functional
            assert clients.live is not None
            assert clients.stat is not None
            assert clients.image is not None
            assert clients.stream is not None
            assert clients.schedule is not None
            assert clients.bgtask is not None
            assert clients.artifact is not None
            assert clients.container_log is not None

            # Test basic operation on live client
            server_time = await clients.live.get_server_time()
            assert server_time > 0

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        manager_config: ManagerUnifiedConfig,
    ) -> None:
        """Dependency should cleanup clients even on exception."""
        dependency = ValkeyDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(manager_config) as clients:
                assert isinstance(clients, ValkeyClients)
                raise RuntimeError("Test error")

        # Clients should be closed - we can't easily verify this,
        # but the test should complete without hanging
