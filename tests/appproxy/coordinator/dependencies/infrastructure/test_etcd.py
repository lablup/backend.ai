from __future__ import annotations

import secrets
from unittest.mock import Mock

import pytest

from ai.backend.appproxy.coordinator.config import ProxyCoordinatorConfig, ServerConfig
from ai.backend.appproxy.coordinator.dependencies.infrastructure.etcd import (
    EtcdProvider,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestEtcdProvider:
    """Test EtcdProvider with real etcd container."""

    @pytest.fixture
    def test_ns(self) -> str:
        """Generate a random namespace for etcd tests."""
        return f"test-{secrets.token_hex(4)}"

    @pytest.fixture
    def coordinator_config_with_traefik(
        self,
        etcd_container: tuple[str, HostPortPairModel],
        test_ns: str,
    ) -> ServerConfig:
        """Create a coordinator config with Traefik enabled."""
        from ai.backend.appproxy.common.config import HostPortPair
        from ai.backend.appproxy.coordinator.config import (
            EtcdConfig,
            ProxyCoordinatorConfig,
            TraefikConfig,
        )

        container_id, etcd_addr = etcd_container

        # Create etcd config
        etcd_config = EtcdConfig(
            addr=HostPortPair(host=etcd_addr.host, port=etcd_addr.port),
            namespace=test_ns,
            password=None,
        )

        # Create traefik config
        traefik_config = TraefikConfig(etcd=etcd_config)

        # Create configs with Mock
        proxy_config = Mock(spec=ProxyCoordinatorConfig)
        proxy_config.enable_traefik = True
        proxy_config.traefik = traefik_config

        config = Mock(spec=ServerConfig)
        config.proxy_coordinator = proxy_config
        return config

    @pytest.fixture
    def coordinator_config_without_traefik(self) -> ServerConfig:
        """Create a coordinator config with Traefik disabled."""
        proxy_config = Mock(spec=ProxyCoordinatorConfig)
        proxy_config.enable_traefik = False

        config = Mock(spec=ServerConfig)
        config.proxy_coordinator = proxy_config
        return config

    @pytest.mark.asyncio
    async def test_provide_traefik_etcd_when_enabled(
        self,
        coordinator_config_with_traefik: ServerConfig,
    ) -> None:
        """Dependency should create TraefikEtcd when enabled."""
        dependency = EtcdProvider()

        async with dependency.provide(coordinator_config_with_traefik) as etcd:
            assert isinstance(etcd, AsyncEtcd)
            # Verify the client is functional by writing and reading
            test_key = "test/key"
            test_value = "test_value"
            await etcd.put(test_key, test_value)
            value = await etcd.get(test_key)
            assert value == test_value

    @pytest.mark.asyncio
    async def test_provide_none_when_disabled(
        self,
        coordinator_config_without_traefik: ServerConfig,
    ) -> None:
        """Dependency should return None when Traefik is disabled."""
        dependency = EtcdProvider()

        async with dependency.provide(coordinator_config_without_traefik) as etcd:
            assert etcd is None

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(
        self,
        coordinator_config_with_traefik: ServerConfig,
    ) -> None:
        """Dependency should cleanup etcd client even on exception."""
        dependency = EtcdProvider()

        with pytest.raises(RuntimeError):
            async with dependency.provide(coordinator_config_with_traefik) as etcd:
                assert isinstance(etcd, AsyncEtcd)
                raise RuntimeError("Test error")

        # Client should be closed - we can't easily verify this,
        # but the test should complete without hanging
