from __future__ import annotations

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.dependencies.bootstrap.config import BootstrapConfig
from ai.backend.manager.dependencies.bootstrap.etcd import EtcdDependency
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestEtcdDependency:
    """Test EtcdDependency with real etcd container."""

    @pytest.fixture
    async def bootstrap_config(
        self,
        etcd_container: tuple[str, HostPortPairModel],
        test_ns: str,
    ) -> BootstrapConfig:
        """Create a bootstrap config pointing to the test etcd container."""
        from ai.backend.common.typed_validators import HostPortPair
        from ai.backend.manager.config.unified import EtcdConfig

        container_id, etcd_addr = etcd_container

        # Create minimal etcd config for testing
        etcd_config = EtcdConfig(
            addr=HostPortPair(host=etcd_addr.host, port=etcd_addr.port),
            namespace=test_ns,
        )

        # Create a minimal BootstrapConfig with just etcd settings
        config = BootstrapConfig(etcd=etcd_config)
        return config

    @pytest.mark.asyncio
    async def test_provide_etcd_client(
        self,
        bootstrap_config: BootstrapConfig,
    ) -> None:
        """Dependency should create and cleanup etcd client."""
        dependency = EtcdDependency()

        async with dependency.provide(bootstrap_config) as etcd:
            assert isinstance(etcd, AsyncEtcd)
            # Verify the client is functional by writing and reading
            await etcd.put("test_key", "test_value")
            value = await etcd.get("test_key")
            assert value == "test_value"

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        bootstrap_config: BootstrapConfig,
    ) -> None:
        """Dependency should cleanup etcd client even on exception."""
        dependency = EtcdDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(bootstrap_config) as etcd:
                assert isinstance(etcd, AsyncEtcd)
                raise RuntimeError("Test error")

        # Client should be closed - we can't easily verify this,
        # but the test should complete without hanging
