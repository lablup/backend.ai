from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.dependencies.infrastructure.redis import (
    RedisProvider,
    RedisProviderInput,
    StorageProxyValkeyClients,
)
from ai.backend.storage.dependencies.infrastructure.redis_config import RedisConfigProvider


class TestRedisProvider:
    """Test RedisProvider with a real Redis container."""

    @pytest.fixture
    def storage_config(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> StorageProxyUnifiedConfig:
        """Create a mock storage config with the Redis settings."""
        _, redis_addr = redis_container
        config = MagicMock(spec=StorageProxyUnifiedConfig)
        config.redis = RedisConfig.model_validate({
            "addr": {"host": redis_addr.host, "port": redis_addr.port},
        })
        return config

    @pytest.mark.integration
    async def test_provide_valkey_clients(
        self,
        storage_config: StorageProxyUnifiedConfig,
    ) -> None:
        """Provider should create and cleanup all Valkey clients."""
        async with RedisConfigProvider().provide(storage_config) as redis_config:
            provider_input = RedisProviderInput(
                redis_config=redis_config, sentinel_monitors=SentinelMonitorSet([]), pidx=0
            )

            async with RedisProvider().provide(provider_input) as clients:
                assert isinstance(clients, StorageProxyValkeyClients)
                # Verify clients are created
                assert clients.bgtask is not None
                assert clients.artifact is not None
                assert clients.tus is not None
                assert clients.volume_stats is not None

    @pytest.mark.integration
    async def test_cleanup_on_exception(
        self,
        storage_config: StorageProxyUnifiedConfig,
    ) -> None:
        """Provider should cleanup clients even on exception."""
        async with RedisConfigProvider().provide(storage_config) as redis_config:
            provider_input = RedisProviderInput(
                redis_config=redis_config, sentinel_monitors=SentinelMonitorSet([]), pidx=0
            )

            with pytest.raises(RuntimeError):
                async with RedisProvider().provide(provider_input) as clients:
                    assert isinstance(clients, StorageProxyValkeyClients)
                    raise RuntimeError("Test error")

        # Clients should be closed - we can't easily verify this,
        # but the test should complete without hanging
