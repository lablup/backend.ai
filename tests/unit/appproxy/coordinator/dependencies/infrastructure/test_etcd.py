from __future__ import annotations

import secrets
from unittest.mock import Mock, patch

import pytest

from ai.backend.appproxy.coordinator.config import (
    ProxyCoordinatorConfig,
    ServerConfig,
    TraefikConfig,
)
from ai.backend.appproxy.coordinator.dependencies.infrastructure.etcd import (
    EtcdProvider,
)
from ai.backend.appproxy.coordinator.errors.config import InvalidTraefikEtcdCredentialsError
from ai.backend.common.configs.etcd import EtcdConfig, EtcdTLSConfig
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
        etcd_config = EtcdConfig(
            addr=HostPortPair(host=etcd_addr.host, port=etcd_addr.port),
            namespace=test_ns,
            user=None,
            password=None,
            keep_alive_interval=5.0,
            keep_alive_timeout=3.0,
            tls=EtcdTLSConfig(
                enabled=False,
                ca_cert=None,
                client_cert=None,
                client_key=None,
                handshake_timeout=None,
            ),
        )

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


class TestEtcdProviderCredentials:
    def _make_config(self, user: str | None, password: str | None) -> ServerConfig:
        etcd_config = EtcdConfig.model_validate({
            "addrs": [HostPortPair(host="127.0.0.1", port=2379)],
            "namespace": "test",
            "user": user,
            "password": password,
        })
        proxy_config = Mock(spec=ProxyCoordinatorConfig)
        proxy_config.enable_traefik = True
        proxy_config.traefik = TraefikConfig(etcd=etcd_config, client_ip_strategy=None)
        config = Mock(spec=ServerConfig)
        config.proxy_coordinator = proxy_config
        return config

    async def test_passes_user_and_password(self) -> None:
        with patch(
            "ai.backend.appproxy.coordinator.dependencies.infrastructure.etcd.TraefikEtcd"
        ) as traefik_etcd_cls:
            async with EtcdProvider().provide(self._make_config("backend", "secret")):
                pass

        assert traefik_etcd_cls.call_args.kwargs["credentials"] == {
            "user": "backend",
            "password": "secret",
        }

    async def test_passes_no_credentials_when_both_unset(self) -> None:
        with patch(
            "ai.backend.appproxy.coordinator.dependencies.infrastructure.etcd.TraefikEtcd"
        ) as traefik_etcd_cls:
            async with EtcdProvider().provide(self._make_config(None, None)):
                pass

        assert traefik_etcd_cls.call_args.kwargs["credentials"] is None

    @pytest.mark.parametrize(
        ("user", "password"),
        [("backend", None), (None, "secret")],
        ids=["user-only", "password-only"],
    )
    async def test_rejects_partial_credentials(
        self, user: str | None, password: str | None
    ) -> None:
        with patch(
            "ai.backend.appproxy.coordinator.dependencies.infrastructure.etcd.TraefikEtcd"
        ) as traefik_etcd_cls:
            with pytest.raises(InvalidTraefikEtcdCredentialsError):
                async with EtcdProvider().provide(self._make_config(user, password)):
                    pass

        traefik_etcd_cls.assert_not_called()
