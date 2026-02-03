from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.appproxy.common.config import HostPortPair
from ai.backend.appproxy.coordinator.config import ProxyCoordinatorConfig
from ai.backend.appproxy.coordinator.dependencies.bootstrap.config import (
    ConfigInput,
    ConfigProvider,
)


@dataclass
class _AdvertiseUrlTestCase:
    """Test case for advertise_base_url property."""

    bind_addr: HostPortPair
    advertised_addr: HostPortPair | None
    tls_listen: bool
    tls_advertised: bool
    expected_url: str
    description: str


class TestProxyCoordinatorConfig:
    """Test ProxyCoordinatorConfig model."""

    @pytest.mark.parametrize(
        "test_case",
        [
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=None,
                tls_listen=False,
                tls_advertised=False,
                expected_url="http://0.0.0.0:10200",
                description="Default bind_addr, no TLS",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=None,
                tls_listen=True,
                tls_advertised=False,
                expected_url="https://0.0.0.0:10200",
                description="Default bind_addr with tls_listen enabled",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=None,
                tls_listen=False,
                tls_advertised=True,
                expected_url="https://0.0.0.0:10200",
                description="Default bind_addr with tls_advertised enabled",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=None,
                tls_listen=True,
                tls_advertised=True,
                expected_url="https://0.0.0.0:10200",
                description="Default bind_addr with both TLS flags enabled",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="192.168.1.100", port=8080),
                advertised_addr=None,
                tls_listen=False,
                tls_advertised=False,
                expected_url="http://192.168.1.100:8080",
                description="Custom bind_addr, no TLS",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=HostPortPair(host="public.example.com", port=443),
                tls_listen=False,
                tls_advertised=False,
                expected_url="http://public.example.com:443",
                description="advertised_addr overrides bind_addr",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=HostPortPair(host="public.example.com", port=443),
                tls_listen=False,
                tls_advertised=True,
                expected_url="https://public.example.com:443",
                description="advertised_addr with TLS",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=HostPortPair(host="http://public.example.com", port=80),
                tls_listen=False,
                tls_advertised=False,
                expected_url="http://public.example.com:80",
                description="advertised_addr with protocol in host (http)",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=HostPortPair(host="https://public.example.com", port=443),
                tls_listen=False,
                tls_advertised=False,
                expected_url="https://public.example.com:443",
                description="advertised_addr with protocol in host (https)",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="0.0.0.0", port=10200),
                advertised_addr=HostPortPair(host="https://public.example.com", port=443),
                tls_listen=True,
                tls_advertised=True,
                expected_url="https://public.example.com:443",
                description="advertised_addr with protocol in host (https), TLS flags ignored",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="http://localhost", port=8080),
                advertised_addr=None,
                tls_listen=False,
                tls_advertised=False,
                expected_url="http://localhost:8080",
                description="bind_addr with protocol in host (http)",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="https://localhost", port=8443),
                advertised_addr=None,
                tls_listen=False,
                tls_advertised=False,
                expected_url="https://localhost:8443",
                description="bind_addr with protocol in host (https)",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="localhost", port=9443),
                advertised_addr=None,
                tls_listen=True,
                tls_advertised=False,
                expected_url="https://localhost:9443",
                description="Custom port with TLS",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="::1", port=10200),
                advertised_addr=None,
                tls_listen=False,
                tls_advertised=False,
                expected_url="http://::1:10200",
                description="IPv6 address without TLS",
            ),
            _AdvertiseUrlTestCase(
                bind_addr=HostPortPair(host="::1", port=10200),
                advertised_addr=None,
                tls_listen=True,
                tls_advertised=False,
                expected_url="https://::1:10200",
                description="IPv6 address with TLS",
            ),
        ],
        ids=lambda tc: tc.description,
    )
    def test_advertise_base_url(
        self,
        test_case: _AdvertiseUrlTestCase,
    ) -> None:
        """Test advertise_base_url property with various configurations."""
        config_data: dict[str, Any] = {
            "bind_addr": test_case.bind_addr,
            "advertised_addr": test_case.advertised_addr,
            "tls_listen": test_case.tls_listen,
            "tls_advertised": test_case.tls_advertised,
            "user": os.getuid(),
            "group": os.getgid(),
        }
        config = ProxyCoordinatorConfig.model_construct(**config_data)

        assert config.advertise_base_url == test_case.expected_url


class TestConfigProvider:
    """Test ConfigProvider lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.appproxy.coordinator.dependencies.bootstrap.config.load")
    async def test_provide_config(self, mock_load: MagicMock) -> None:
        """Dependency should load config from file."""
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        dependency = ConfigProvider()
        config_input = ConfigInput(config_path=Path("/test/config.toml"))

        async with dependency.provide(config_input) as config:
            assert config is mock_config
            mock_load.assert_called_once_with(Path("/test/config.toml"))

    @pytest.mark.asyncio
    @patch("ai.backend.appproxy.coordinator.dependencies.bootstrap.config.load")
    async def test_provide_config_with_none_path(self, mock_load: MagicMock) -> None:
        """Dependency should handle None config path."""
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        dependency = ConfigProvider()
        config_input = ConfigInput(config_path=None)

        async with dependency.provide(config_input) as config:
            assert config is mock_config
            mock_load.assert_called_once_with(None)
