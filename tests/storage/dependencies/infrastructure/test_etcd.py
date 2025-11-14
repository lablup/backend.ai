from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.storage.config.unified import EtcdConfig, StorageProxyUnifiedConfig
from ai.backend.storage.dependencies.infrastructure.etcd import EtcdProvider
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestEtcdProvider:
    """Test EtcdProvider with real etcd container."""

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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_provide_etcd_client(
        self,
        storage_config: StorageProxyUnifiedConfig,
    ) -> None:
        """Provider should create and cleanup etcd client."""
        provider = EtcdProvider()

        async with provider.provide(storage_config) as etcd:
            assert isinstance(etcd, AsyncEtcd)
            # Verify the client is functional by writing and reading
            await etcd.put("test_key", "test_value")
            value = await etcd.get("test_key")
            assert value == "test_value"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        storage_config: StorageProxyUnifiedConfig,
    ) -> None:
        """Provider should cleanup etcd client even on exception."""
        provider = EtcdProvider()

        with pytest.raises(RuntimeError):
            async with provider.provide(storage_config) as etcd:
                assert isinstance(etcd, AsyncEtcd)
                raise RuntimeError("Test error")

        # Client should be closed - we can't easily verify this,
        # but the test should complete without hanging
