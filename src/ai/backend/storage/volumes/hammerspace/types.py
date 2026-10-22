from ai.backend.common.types import BackendAISchema


class SSLConfig(BackendAISchema):
    cert_file: str | None
    key_file: str | None
