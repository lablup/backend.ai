"""
Request DTOs for group (project) system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "RegistryQuotaRequest",
    "RegistryQuotaReadRequest",
)


class RegistryQuotaRequest(BaseRequestModel):
    """Request to create or update a registry quota for a project."""

    group_id: UUID = Field(
        validation_alias=AliasChoices("group_id", "group"),
        description="Project (group) ID",
    )
    quota: int = Field(description="Registry quota value in bytes")


class RegistryQuotaReadRequest(BaseRequestModel):
    """Request to read or delete a registry quota for a project."""

    group_id: UUID = Field(
        validation_alias=AliasChoices("group_id", "group"),
        description="Project (group) ID",
    )
