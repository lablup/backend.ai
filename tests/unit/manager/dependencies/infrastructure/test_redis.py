from __future__ import annotations

import pytest

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import RedisRole
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import HostPortPair
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.infrastructure.redis import (
    ValkeyClients,
    ValkeyDependency,
)


class TestValkeyDependency:
    """Test ValkeyDependency with real Redis container."""

    @pytest.fixture
    def manager_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> ManagerUnifiedConfig:
        """Create a manager config pointing to the test redis container."""
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
        return ManagerUnifiedConfig(redis=redis_config)  # type: ignore[call-arg]

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


class TestValkeyDependencyLoginSessionDatabase:
    @pytest.fixture
    def manager_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> ManagerUnifiedConfig:
        _container_id, redis_addr = redis_container
        return ManagerUnifiedConfig.model_validate({
            "redis": {"addr": {"host": redis_addr.host, "port": redis_addr.port}},
            "auth": {"login-session-db": 10},
        })

    async def _client_on(
        self, manager_config: ManagerUnifiedConfig, db: int
    ) -> ValkeySessionClient:
        target = manager_config.redis.to_valkey_profile_target().profile_target(
            RedisRole.STATISTICS
        )
        return await ValkeySessionClient.create(
            target, db_id=db, human_readable_name="test.manager.session"
        )

    async def test_login_sessions_are_stored_in_the_configured_database(
        self,
        manager_config: ManagerUnifiedConfig,
    ) -> None:
        async with ValkeyDependency().provide(manager_config) as clients:
            await clients.session.set_login_session("BAI-911-manager", "data", 60)

        configured_db = await self._client_on(manager_config, 10)
        default_db = await self._client_on(manager_config, 0)
        try:
            assert await configured_db.get_login_session("BAI-911-manager") == b"data"
            assert await default_db.get_login_session("BAI-911-manager") is None
        finally:
            await configured_db.delete_login_session("BAI-911-manager")
            await configured_db.close()
            await default_db.close()
