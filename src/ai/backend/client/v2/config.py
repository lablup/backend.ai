from __future__ import annotations

from dataclasses import dataclass

from yarl import URL

from ai.backend.client.config import APIConfig


@dataclass(frozen=True)
class ClientConfig:
    endpoint: URL
    api_version: str = "v9.20250722"
    connection_timeout: float = 10.0
    read_timeout: float = 0
    skip_ssl_verification: bool = False

    @classmethod
    def from_v1_config(cls, api_config: APIConfig) -> ClientConfig:
        """Create a V2 ClientConfig from a V1 APIConfig."""
        return cls(
            endpoint=api_config.endpoint,
            skip_ssl_verification=api_config.skip_sslcert_validation,
            connection_timeout=api_config.connection_timeout,
            read_timeout=api_config.read_timeout,
        )
