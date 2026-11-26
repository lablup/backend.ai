from __future__ import annotations

import pytest

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.config import redis_config_iv
from ai.backend.common.defs import RedisRole
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import HostPortPair
from ai.backend.web.config.unified import SessionConfig, WebServerUnifiedConfig
from ai.backend.web.dependencies.infrastructure.redis import RedisProvider, RedisProviderInput


class TestRedisProvider:
    """Test RedisProvider with real Redis container."""

    @pytest.fixture
    def web_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> WebServerUnifiedConfig:
        """Create a web config pointing to the test redis container."""
        _container_id, redis_addr = redis_container

        # Create Redis config with single endpoint for all roles
        redis_config_data = {
            "addr": HostPortPair(host=redis_addr.host, port=redis_addr.port),
            "sentinel": None,
            "service_name": None,
            "password": None,
        }
        redis_config = redis_config_iv.check(redis_config_data)

        # Create minimal WebServerUnifiedConfig with just session.redis settings
        session_config = SessionConfig(redis=redis_config)  # type: ignore[call-arg]
        return WebServerUnifiedConfig(session=session_config)  # type: ignore[call-arg]

    async def test_provide_redis_client(
        self,
        web_config: WebServerUnifiedConfig,
    ) -> None:
        """Provider should create and cleanup Valkey session client."""
        provider = RedisProvider()

        async with provider.provide(
            RedisProviderInput(config=web_config, sentinel_monitors=SentinelMonitorSet([]))
        ) as client:
            assert isinstance(client, ValkeySessionClient)
            # Verify client is functional
            server_time = await client.get_server_time_second()
            assert server_time > 0

    async def test_cleanup_on_exception(
        self,
        web_config: WebServerUnifiedConfig,
    ) -> None:
        """Provider should cleanup client even on exception."""
        provider = RedisProvider()

        with pytest.raises(RuntimeError):
            async with provider.provide(
                RedisProviderInput(config=web_config, sentinel_monitors=SentinelMonitorSet([]))
            ) as client:
                assert isinstance(client, ValkeySessionClient)
                raise RuntimeError("Test error")

        # Client should be closed - we can't easily verify this,
        # but the test should complete without hanging

    async def test_stage_name(self) -> None:
        """Provider should have correct stage name."""
        provider = RedisProvider()
        assert provider.stage_name == "redis"


class TestRedisProviderDatabase:
    @pytest.fixture
    def web_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> WebServerUnifiedConfig:
        _container_id, redis_addr = redis_container
        return WebServerUnifiedConfig.model_validate({
            "session": {
                "redis": {"addr": {"host": redis_addr.host, "port": redis_addr.port}, "db": 10}
            }
        })

    async def _client_on(self, web_config: WebServerUnifiedConfig, db: int) -> ValkeySessionClient:
        target = web_config.session.redis.to_valkey_profile_target().profile_target(
            RedisRole.STATISTICS
        )
        return await ValkeySessionClient.create(
            target, db_id=db, human_readable_name="test.web.session"
        )

    async def test_sessions_are_stored_in_the_configured_database(
        self,
        web_config: WebServerUnifiedConfig,
    ) -> None:
        async with RedisProvider().provide(
            RedisProviderInput(config=web_config, sentinel_monitors=SentinelMonitorSet([]))
        ) as client:
            await client.set_session_data("BAI-911-web", b"data", ttl_seconds=60)

        configured_db = await self._client_on(web_config, 10)
        default_db = await self._client_on(web_config, 0)
        try:
            assert await configured_db.get_session_data("BAI-911-web") == b"data"
            assert await default_db.get_session_data("BAI-911-web") is None
        finally:
            await configured_db.delete_session_data("BAI-911-web")
            await configured_db.close()
            await default_db.close()
