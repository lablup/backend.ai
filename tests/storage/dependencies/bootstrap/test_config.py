from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.common.typed_validators import HostPortPair
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.dependencies.bootstrap.config import ConfigProvider, ConfigProviderInput


class TestConfigProvider:
    """Test ConfigProvider for loading storage proxy configuration."""

    @pytest.fixture
    def config_path(self, tmp_path: Path) -> Path:
        """Create a minimal test config file."""
        config_file = tmp_path / "storage-proxy.toml"
        config_file.write_text(
            """
[etcd]
namespace = "local"
addr = { host = "127.0.0.1", port = 2379 }

[redis]
addr = { host = "127.0.0.1", port = 6379 }

[storage-proxy]
event-loop = "asyncio"
pid-file = "/tmp/storage-proxy.pid"
node-id = "i-test-storage-proxy"
secret = "test-secret-for-storage-proxy"
session-expire = "1d"

[api.client]
service-addr = { host = "0.0.0.0", port = 6021 }
ssl-enabled = false

[api.manager]
service-addr = { host = "0.0.0.0", port = 6022 }
ssl-enabled = false
secret = "test-secret-shared-with-manager"

[volume.test]
backend = "vfs"
path = "/tmp/backend.ai/vfroot/local"
"""
        )
        return config_file

    async def test_provide_config(
        self,
        config_path: Path,
    ) -> None:
        """Provider should load and provide configuration."""
        provider = ConfigProvider()
        provider_input = ConfigProviderInput(config_path=config_path)

        async with provider.provide(provider_input) as config:
            assert isinstance(config, StorageProxyUnifiedConfig)
            assert config.etcd.namespace == "local"
            assert isinstance(config.etcd.addr, HostPortPair)
            assert config.etcd.addr.host == "127.0.0.1"
            assert config.etcd.addr.port == 2379

    async def test_cleanup_on_exception(
        self,
        config_path: Path,
    ) -> None:
        """Provider should handle exceptions gracefully."""
        provider = ConfigProvider()
        provider_input = ConfigProviderInput(config_path=config_path)

        with pytest.raises(RuntimeError):
            async with provider.provide(provider_input) as config:
                assert isinstance(config, StorageProxyUnifiedConfig)
                raise RuntimeError("Test error")
