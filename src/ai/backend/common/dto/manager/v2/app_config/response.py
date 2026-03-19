"""
Response DTOs for app_config DTO v2.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AppConfigNode",
    "DeleteDomainConfigPayload",
    "DeleteUserConfigPayload",
)


class AppConfigNode(BaseResponseModel):
    """Node model representing app configuration data."""

    extra_config: dict[str, Any] = Field(description="Additional configuration data.")


class DeleteDomainConfigPayload(BaseResponseModel):
    """Payload for domain-level app config deletion mutation result."""

    deleted: bool = Field(description="Whether the deletion was successful.")


class DeleteUserConfigPayload(BaseResponseModel):
    """Payload for user-level app config deletion mutation result."""

    deleted: bool = Field(description="Whether the deletion was successful.")
