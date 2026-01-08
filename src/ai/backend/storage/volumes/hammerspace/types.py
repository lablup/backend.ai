from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel
from yarl import URL


class SSLConfig(BaseModel):
    cert_file: Optional[str]
    key_file: Optional[str]


@dataclass
class APIConnectionInfo:
    address: URL
    username: str
    password: str
    ssl_enabled: bool
    ssl_config: Optional[SSLConfig]
