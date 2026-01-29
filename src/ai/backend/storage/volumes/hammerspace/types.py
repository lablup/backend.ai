from dataclasses import dataclass

from pydantic import BaseModel
from yarl import URL


class SSLConfig(BaseModel):
    cert_file: str | None
    key_file: str | None


@dataclass
class APIConnectionInfo:
    address: URL
    username: str
    password: str
    ssl_enabled: bool
    ssl_config: SSLConfig | None
