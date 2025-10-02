from dataclasses import dataclass
from typing import Optional

from yarl import URL


@dataclass
class SSLConfig:
    cert_file: Optional[str]
    key_file: Optional[str]


@dataclass
class ConnectionInfo:
    address: URL
    username: str
    password: str
    ssl_enabled: bool
    ssl_config: Optional[SSLConfig]
