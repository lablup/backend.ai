"""
Response DTOs for group (project) system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("RegistryQuotaReadResponse",)


class RegistryQuotaReadResponse(BaseResponseModel):
    """Response containing the registry quota for a project."""

    result: int = Field(description="Registry quota value in bytes")
