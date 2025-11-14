from __future__ import annotations

import pytest

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.testutils.bootstrap import HostPortPairModel
from ai.backend.web.config.unified import WebServerUnifiedConfig
from ai.backend.web.dependencies.infrastructure.redis import RedisProvider


class TestRedisProvider:
    """Test RedisProvider with real Redis container."""

    @pytest.fixture
    def web_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> WebServerUnifiedConfig:
        """Create a web config pointing to the test redis container."""
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

        # Create minimal WebServerUnifiedConfig with just session.redis settings
        from ai.backend.web.config.unified import SessionConfig

        session_config = SessionConfig(redis=redis_config)  # type: ignore[call-arg]
        config = WebServerUnifiedConfig(session=session_config)  # type: ignore[call-arg]
        return config

    @pytest.mark.asyncio
    async def test_provide_redis_client(
        self,
        web_config: WebServerUnifiedConfig,
    ) -> None:
        """Provider should create and cleanup Valkey session client."""
        provider = RedisProvider()

        async with provider.provide(web_config) as client:
            assert isinstance(client, ValkeySessionClient)
            # Verify client is functional
            server_time = await client.get_server_time_second()
            assert server_time > 0

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        web_config: WebServerUnifiedConfig,
    ) -> None:
        """Provider should cleanup client even on exception."""
        provider = RedisProvider()

        with pytest.raises(RuntimeError):
            async with provider.provide(web_config) as client:
                assert isinstance(client, ValkeySessionClient)
                raise RuntimeError("Test error")

        # Client should be closed - we can't easily verify this,
        # but the test should complete without hanging

    @pytest.mark.asyncio
    async def test_stage_name(self) -> None:
        """Provider should have correct stage name."""
        provider = RedisProvider()
        assert provider.stage_name == "redis"
