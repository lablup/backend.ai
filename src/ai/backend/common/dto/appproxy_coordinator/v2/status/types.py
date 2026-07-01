from ai.backend.common.types import BackendAISchema


class AppProxyStatusResponse(BackendAISchema):
    """Response from AppProxy /status endpoint."""

    api_version: str
    advertise_address: str | None = None
