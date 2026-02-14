from dataclasses import dataclass

from yarl import URL

from ai.backend.client.config import API_VERSION, get_env


@dataclass(frozen=True)
class ClientConfig:
    endpoint: URL
    api_version: str = f"v{API_VERSION[0]}.{API_VERSION[1]}"
    connection_timeout: float = 10.0
    read_timeout: float = 0
    skip_ssl_verification: bool = False

    @classmethod
    def from_env(cls) -> "ClientConfig":
        endpoint: str = get_env("ENDPOINT", "https://api.cloud.backend.ai")
        connection_timeout: float = get_env("CONNECTION_TIMEOUT", "10.0", clean=float)
        read_timeout: float = get_env("READ_TIMEOUT", "0", clean=float)
        return cls(
            endpoint=URL(endpoint),
            connection_timeout=connection_timeout,
            read_timeout=read_timeout,
        )
