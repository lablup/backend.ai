from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class StreamProxyRequest(BaseRequestModel):
    """Request parameters for the stream proxy endpoint."""

    app: str = Field(validation_alias="app")
    port: int | None = Field(default=None, ge=1024, le=65535)
    envs: str | None = Field(default=None)
    arguments: str | None = Field(default=None)


class SessionNamePath(BaseRequestModel):
    """Path parameter for session name."""

    session_name: str
