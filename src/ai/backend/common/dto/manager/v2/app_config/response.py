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
    "UpsertDomainConfigPayloadDTO",
    "UpsertUserConfigPayloadDTO",
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


class UpsertDomainConfigPayloadDTO(BaseResponseModel):
    """Payload returned after upserting domain-level app configuration."""

    app_config: AppConfigNode = Field(description="The resulting app configuration")


class UpsertUserConfigPayloadDTO(BaseResponseModel):
    """Payload returned after upserting user-level app configuration."""

    app_config: AppConfigNode = Field(description="The resulting app configuration")
