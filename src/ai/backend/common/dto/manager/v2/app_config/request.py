"""
Request DTOs for App Configuration v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "DeleteDomainConfigInput",
    "DeleteUserConfigInput",
    "UpsertDomainConfigInput",
    "UpsertUserConfigInput",
)


class UpsertDomainConfigInput(BaseRequestModel):
    """Input for creating or updating domain-level app configuration."""

    domain_name: str = Field(description="Domain name whose configuration will be upserted.")
    extra_config: dict[str, Any] = Field(
        description="Configuration data to store. Completely replaces existing configuration."
    )


class UpsertUserConfigInput(BaseRequestModel):
    """Input for creating or updating user-level app configuration."""

    extra_config: dict[str, Any] = Field(
        description="Configuration data to store. Completely replaces existing configuration."
    )
    user_id: UUID | None = Field(
        default=None,
        description="User ID whose configuration will be upserted. Defaults to current user.",
    )


class DeleteDomainConfigInput(BaseRequestModel):
    """Input for deleting domain-level app configuration."""

    domain_name: str = Field(description="Domain name whose configuration will be deleted.")


class DeleteUserConfigInput(BaseRequestModel):
    """Input for deleting user-level app configuration."""

    user_id: UUID | None = Field(
        default=None,
        description="User ID whose configuration will be deleted. Defaults to current user.",
    )
