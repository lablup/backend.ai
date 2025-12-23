from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.storage.config.unified import EtcdConfig, StorageProxyUnifiedConfig
from ai.backend.storage.dependencies.infrastructure.redis import (
    RedisProvider,
    StorageProxyValkeyClients,
)
from ai.backend.testutils.bootstrap import HostPortPairModel


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
        )
        return config

    @pytest.fixture
    async def etcd_client(
        self,
        storage_config: StorageProxyUnifiedConfig,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[AsyncEtcd, None]:
        """Create an etcd client for testing."""
        from ai.backend.storage.config.loaders import make_etcd

        redis_container_id, redis_addr = redis_container

        etcd = make_etcd(storage_config)
        try:
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
        finally:
            await etcd.close()

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
