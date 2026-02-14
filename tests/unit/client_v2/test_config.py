from unittest import mock

import pytest
from yarl import URL

from ai.backend.client.config import API_VERSION
from ai.backend.client.v2.config import ClientConfig


class TestClientConfig:
    def test_creation_with_defaults(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        assert config.endpoint == URL("https://api.example.com")
        assert config.api_version == f"v{API_VERSION[0]}.{API_VERSION[1]}"
        assert config.connection_timeout == 10.0
        assert config.read_timeout == 0
        assert config.skip_ssl_verification is False

    def test_creation_with_custom_values(self) -> None:
        config = ClientConfig(
            endpoint=URL("https://custom.api.com"),
            api_version="v8.20240101",
            connection_timeout=30.0,
            read_timeout=60.0,
            skip_ssl_verification=True,
        )
        assert config.endpoint == URL("https://custom.api.com")
        assert config.api_version == "v8.20240101"
        assert config.connection_timeout == 30.0
        assert config.read_timeout == 60.0
        assert config.skip_ssl_verification is True

    def test_frozen_dataclass(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        with pytest.raises(AttributeError):
            config.endpoint = URL("https://other.com")  # type: ignore[misc]

    def test_from_env(self) -> None:
        env_vars = {
            "BACKEND_ENDPOINT": "https://env.api.com",
            "BACKEND_CONNECTION_TIMEOUT": "20.0",
            "BACKEND_READ_TIMEOUT": "5.0",
        }
        with mock.patch.dict("os.environ", env_vars, clear=False):
            config = ClientConfig.from_env()
        assert config.endpoint == URL("https://env.api.com")
        assert config.connection_timeout == 20.0
        assert config.read_timeout == 5.0
