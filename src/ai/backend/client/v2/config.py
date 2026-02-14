from dataclasses import dataclass

from yarl import URL


@dataclass(frozen=True)
class ClientConfig:
    endpoint: URL
    api_version: str = "v9.20250722"
    connection_timeout: float = 10.0
    read_timeout: float = 0
    skip_ssl_verification: bool = False
