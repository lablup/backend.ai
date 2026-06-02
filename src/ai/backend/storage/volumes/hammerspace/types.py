from dataclasses import dataclass

from yarl import URL

from ai.backend.common.types import BackendAISchema


class SSLConfig(BackendAISchema):
    cert_file: str | None
    key_file: str | None


@dataclass
class APIConnectionInfo:
    address: URL
    username: str
    password: str
    ssl_enabled: bool
    ssl_config: SSLConfig | None
