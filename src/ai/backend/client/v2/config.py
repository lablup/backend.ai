from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from yarl import URL

from ai.backend.client.config import APIConfig

if TYPE_CHECKING:
    import aiohttp


@dataclass(frozen=True)
class ClientConfig:
    endpoint: URL
    endpoint_type: str = "api"
    api_version: str = "v9.20250722"
    connection_timeout: float = 10.0
    read_timeout: float = 0
    skip_ssl_verification: bool = False
    cookie_jar: aiohttp.CookieJar | None = field(default=None)

    @classmethod
    def from_v1_config(cls, api_config: APIConfig) -> ClientConfig:
        """Create a V2 ClientConfig from a V1 APIConfig."""
        return cls(
            endpoint=api_config.endpoint,
            endpoint_type=api_config.endpoint_type,
            skip_ssl_verification=api_config.skip_sslcert_validation,
            connection_timeout=api_config.connection_timeout,
            read_timeout=api_config.read_timeout,
        )
