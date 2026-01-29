from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.storage.config.loaders import make_etcd
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.dependencies.infrastructure.redis import (
    RedisProvider,
    StorageProxyValkeyClients,
)


class TestRedisProvider:
    """Test RedisProvider with real Redis and etcd containers."""

    @pytest.fixture
    def storage_config(
        self,
        etcd_container: tuple[str, HostPortPairModel],
        test_ns: str,
    ) -> StorageProxyUnifiedConfig:
        """Create a mock storage config with etcd settings."""
        container_id, etcd_addr = etcd_container

        # Create mock config with only etcd settings
        config = MagicMock(spec=StorageProxyUnifiedConfig)
        config.etcd = EtcdConfig(
            addr=HostPortPair(host=etcd_addr.host, port=etcd_addr.port),
            namespace=test_ns,
            user=None,
            password=None,
        )
        return config

    @pytest.fixture
    async def etcd_client(
        self,
        storage_config: StorageProxyUnifiedConfig,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[AsyncEtcd, None]:
        """Create an etcd client for testing."""
        redis_container_id, redis_addr = redis_container

        async with make_etcd(storage_config) as etcd:
            # Store redis config in etcd for RedisProvider
            await etcd.put_prefix(
                "config/redis",
                {
                    "addr": {
                        "host": redis_addr.host,
                        "port": str(redis_addr.port),
                    },
                },
            )
            yield etcd

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_provide_valkey_clients(
        self,
        etcd_client: AsyncEtcd,
    ) -> None:
        """Provider should create and cleanup all Valkey clients."""
        provider = RedisProvider()

        async with provider.provide(etcd_client) as clients:
            assert isinstance(clients, StorageProxyValkeyClients)
            # Verify clients are created
            assert clients.bgtask is not None
            assert clients.artifact is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        etcd_client: AsyncEtcd,
    ) -> None:
        """Provider should cleanup clients even on exception."""
        provider = RedisProvider()

        with pytest.raises(RuntimeError):
            async with provider.provide(etcd_client) as clients:
                assert isinstance(clients, StorageProxyValkeyClients)
                raise RuntimeError("Test error")

        # Clients should be closed - we can't easily verify this,
        # but the test should complete without hanging
