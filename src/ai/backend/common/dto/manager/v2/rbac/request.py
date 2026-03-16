"""
Request DTOs for RBAC DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

from .types import RoleSource, RoleStatus

__all__ = (
    "CreateRoleInput",
    "DeleteRoleInput",
    "PurgeRoleInput",
    "UpdateRoleInput",
)


class CreateRoleInput(BaseRequestModel):
    """Input for creating a role."""

    name: str = Field(min_length=1, max_length=256, description="Role name")
    description: str | None = Field(default=None, description="Role description")
    source: RoleSource = Field(default=RoleSource.CUSTOM, description="Role source")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class UpdateRoleInput(BaseRequestModel):
    """Input for updating a role."""

    name: str | None = Field(default=None, description="Updated role name")
    description: str | Sentinel | None = Field(
        default=SENTINEL, description="Updated role description. Use SENTINEL to clear."
    )
    status: RoleStatus | None = Field(default=None, description="Updated role status")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteRoleInput(BaseRequestModel):
    """Input for soft-deleting a role."""

    id: UUID = Field(description="Role ID to delete")


class PurgeRoleInput(BaseRequestModel):
    """Input for purging a role."""

    id: UUID = Field(description="Role ID to purge")
