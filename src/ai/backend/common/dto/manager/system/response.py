from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("SystemVersionResponse",)


class SystemVersionResponse(BaseResponseModel):
    """Response for system version info from GET /."""

    version: str = Field(description="API version string")
    manager: str = Field(description="Manager version string")
