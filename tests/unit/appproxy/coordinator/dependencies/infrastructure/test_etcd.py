from __future__ import annotations

import secrets
from unittest.mock import MagicMock, Mock, patch

import pytest
from etcd_client import Client as EtcdClient

from ai.backend.appproxy.coordinator.config import (
    ProxyCoordinatorConfig,
    ServerConfig,
    TraefikConfig,
)
from ai.backend.appproxy.coordinator.dependencies.infrastructure.etcd import (
    EtcdProvider,
)
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel


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
        container_id, etcd_addr = etcd_container

        # Create etcd config
        etcd_config = EtcdConfig.model_validate({
            "addrs": [HostPortPair(host=etcd_addr.host, port=etcd_addr.port)],
            "namespace": test_ns,
            "user": None,
            "password": None,
        })

        # Create traefik config
        traefik_config = TraefikConfig(etcd=etcd_config, client_ip_strategy=None)

        # Create configs with Mock
        proxy_config = Mock(spec=ProxyCoordinatorConfig)
        proxy_config.enable_traefik = True
        proxy_config.traefik = traefik_config

        config = Mock(spec=ServerConfig)
        config.proxy_coordinator = proxy_config
        return config

    @pytest.fixture
    def coordinator_config_with_three_addrs(
        self,
        etcd_container: tuple[str, HostPortPairModel],
        test_ns: str,
    ) -> ServerConfig:
        _, etcd_addr = etcd_container
        etcd_config = EtcdConfig.model_validate({
            "addrs": [HostPortPair(host=etcd_addr.host, port=etcd_addr.port)] * 3,
            "namespace": test_ns,
        })
        proxy_config = Mock(spec=ProxyCoordinatorConfig)
        proxy_config.enable_traefik = True
        proxy_config.traefik = TraefikConfig(etcd=etcd_config, client_ip_strategy=None)
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

    async def test_provide_uses_every_addr_on_one_connection(
        self,
        etcd_container: tuple[str, HostPortPairModel],
        coordinator_config_with_three_addrs: ServerConfig,
    ) -> None:
        _, etcd_addr = etcd_container
        unused_client = MagicMock()
        unused_client.connect.side_effect = AssertionError("opened TraefikEtcd connected again")

        with patch("ai.backend.common.etcd.EtcdClient", wraps=EtcdClient) as etcd_client_cls:
            async with EtcdProvider().provide(coordinator_config_with_three_addrs) as etcd:
                assert etcd is not None
                with patch.object(etcd, "etcd", unused_client):
                    await etcd.put("multi-addr", "1")
                    assert await etcd.get("multi-addr") == "1"
                    await etcd.delete("multi-addr")

        assert (
            etcd_client_cls.call_args.args[0] == [f"http://{etcd_addr.host}:{etcd_addr.port}"] * 3
        )

    async def test_provide_none_when_disabled(
        self,
        coordinator_config_without_traefik: ServerConfig,
    ) -> None:
        """Dependency should return None when Traefik is disabled."""
        dependency = EtcdProvider()

        async with dependency.provide(coordinator_config_without_traefik) as etcd:
            assert etcd is None

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
