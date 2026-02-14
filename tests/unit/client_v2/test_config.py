import pytest
from yarl import URL

from ai.backend.client.v2.config import ClientConfig


class TestClientConfig:
    def test_creation_with_defaults(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        assert config.endpoint == URL("https://api.example.com")
        assert config.api_version == "v9.20250722"
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
