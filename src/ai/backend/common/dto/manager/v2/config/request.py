"""
Request DTOs for config DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

from .types import MAXIMUM_DOTFILE_SIZE, DotfilePermission, DotfileScope

__all__ = (
    "CreateDotfileInput",
    "DeleteDotfileInput",
    "UpdateBootstrapScriptInput",
    "UpdateDotfileInput",
)


class CreateDotfileInput(BaseRequestModel):
    """Input for creating a dotfile."""

    scope: DotfileScope = Field(description="Dotfile scope (user, group, domain)")
    path: str = Field(min_length=1, description="Dotfile path")
    data: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Dotfile content",
    )
    permission: DotfilePermission = Field(description="Unix file permission in octal (e.g., '755')")
    domain: str | None = Field(default=None, description="Domain name")
    group_id: UUID | None = Field(default=None, description="Group UUID")
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the target user (for superadmin delegation)",
    )

    @field_validator("path")
    @classmethod
    def path_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("path must not be blank or whitespace-only")
        return stripped


class UpdateDotfileInput(BaseRequestModel):
    """Input for updating a dotfile."""

    path: str = Field(description="Dotfile path")
    data: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated dotfile content. Use SENTINEL to clear.",
    )
    permission: DotfilePermission | None = Field(
        default=None,
        description="Updated Unix file permission in octal (e.g., '755')",
    )

    @field_validator("path")
    @classmethod
    def path_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("path must not be blank or whitespace-only")
        return stripped


class DeleteDotfileInput(BaseRequestModel):
    """Input for deleting a dotfile."""

    path: str = Field(min_length=1, description="Dotfile path to delete")

    @field_validator("path")
    @classmethod
    def path_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("path must not be blank or whitespace-only")
        return stripped


class UpdateBootstrapScriptInput(BaseRequestModel):
    """Input for updating the bootstrap script."""

    script: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Bootstrap script content",
    )
