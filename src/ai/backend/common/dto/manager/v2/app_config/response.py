"""
Response DTOs for app_config DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "DeleteDomainConfigPayload",
    "DeleteUserConfigPayload",
)


class DeleteDomainConfigPayload(BaseResponseModel):
    """Payload for domain-level app config deletion mutation result."""

    deleted: bool = Field(description="Whether the deletion was successful.")


class DeleteUserConfigPayload(BaseResponseModel):
    """Payload for user-level app config deletion mutation result."""

    deleted: bool = Field(description="Whether the deletion was successful.")
