"""
Request DTOs for config (dotfile) system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import AliasChoices, Field, field_validator, model_validator

from ai.backend.common import msgpack
from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.config.types import (
    MAXIMUM_DOTFILE_SIZE,
    RESERVED_DOTFILES,
    DotfilePermission,
)
from ai.backend.common.exception import InvalidAPIParameters

__all__ = (
    # User config
    "CreateUserDotfileRequest",
    "GetUserDotfileRequest",
    "UpdateUserDotfileRequest",
    "DeleteUserDotfileRequest",
    "UpdateBootstrapScriptRequest",
    "GetBootstrapScriptRequest",
    # Group config
    "CreateGroupDotfileRequest",
    "GetGroupDotfileRequest",
    "UpdateGroupDotfileRequest",
    "DeleteGroupDotfileRequest",
    # Domain config
    "CreateDomainDotfileRequest",
    "GetDomainDotfileRequest",
    "UpdateDomainDotfileRequest",
    "DeleteDomainDotfileRequest",
)


# ---- User Config ----


class CreateUserDotfileRequest(BaseRequestModel):
    """Request to create a user dotfile."""

    path: str = Field(description="Dotfile path")
    data: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Dotfile content",
    )
    permission: DotfilePermission = Field(description="Unix file permission in octal (e.g., '755')")
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the target user (for superadmin delegation)",
    )

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if value in RESERVED_DOTFILES:
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")
        return value

    @model_validator(mode="after")
    def validate_serialized_size(self) -> Self:
        packed = msgpack.packb([{"path": self.path, "perm": self.permission, "data": self.data}])
        if len(packed) > MAXIMUM_DOTFILE_SIZE:
            raise InvalidAPIParameters("No leftover space for dotfile storage")
        return self


class GetUserDotfileRequest(BaseRequestModel):
    """Request to list or get user dotfiles."""

    path: str | None = Field(
        default=None,
        description="Dotfile path to retrieve; if omitted, lists all dotfiles",
    )
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the target user (for superadmin delegation)",
    )


class UpdateUserDotfileRequest(BaseRequestModel):
    """Request to update a user dotfile."""

    path: str = Field(description="Dotfile path")
    data: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Updated dotfile content",
    )
    permission: DotfilePermission = Field(description="Unix file permission in octal (e.g., '755')")
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the target user (for superadmin delegation)",
    )


class DeleteUserDotfileRequest(BaseRequestModel):
    """Request to delete a user dotfile."""

    path: str = Field(description="Dotfile path to delete")
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the target user (for superadmin delegation)",
    )


class UpdateBootstrapScriptRequest(BaseRequestModel):
    """Request to update the bootstrap script."""

    script: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Bootstrap script content",
    )


class GetBootstrapScriptRequest(BaseRequestModel):
    """Request to get the bootstrap script. No parameters required."""


# ---- Group Config ----


class CreateGroupDotfileRequest(BaseRequestModel):
    """Request to create a group dotfile."""

    group: UUID | str = Field(
        validation_alias=AliasChoices("group", "groupId", "group_id"),
        description="Group UUID or name",
    )
    domain: str | None = Field(
        default=None,
        description="Domain name (required when group is specified by name)",
    )
    path: str = Field(description="Dotfile path")
    data: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Dotfile content",
    )
    permission: DotfilePermission = Field(description="Unix file permission in octal (e.g., '755')")


class GetGroupDotfileRequest(BaseRequestModel):
    """Request to list or get group dotfiles."""

    group: UUID | str = Field(
        validation_alias=AliasChoices("group", "groupId", "group_id"),
        description="Group UUID or name",
    )
    domain: str | None = Field(
        default=None,
        description="Domain name (required when group is specified by name)",
    )
    path: str | None = Field(
        default=None,
        description="Dotfile path to retrieve; if omitted, lists all dotfiles",
    )


class UpdateGroupDotfileRequest(BaseRequestModel):
    """Request to update a group dotfile."""

    group: UUID | str = Field(
        validation_alias=AliasChoices("group", "groupId", "group_id"),
        description="Group UUID or name",
    )
    domain: str | None = Field(
        default=None,
        description="Domain name (required when group is specified by name)",
    )
    path: str = Field(description="Dotfile path")
    data: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Updated dotfile content",
    )
    permission: DotfilePermission = Field(description="Unix file permission in octal (e.g., '755')")


class DeleteGroupDotfileRequest(BaseRequestModel):
    """Request to delete a group dotfile."""

    group: UUID | str = Field(
        validation_alias=AliasChoices("group", "groupId", "group_id"),
        description="Group UUID or name",
    )
    domain: str | None = Field(
        default=None,
        description="Domain name (required when group is specified by name)",
    )
    path: str = Field(description="Dotfile path to delete")


# ---- Domain Config ----


class CreateDomainDotfileRequest(BaseRequestModel):
    """Request to create a domain dotfile."""

    domain: str = Field(description="Domain name")
    path: str = Field(description="Dotfile path")
    data: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Dotfile content",
    )
    permission: DotfilePermission = Field(description="Unix file permission in octal (e.g., '755')")


class GetDomainDotfileRequest(BaseRequestModel):
    """Request to list or get domain dotfiles."""

    domain: str = Field(description="Domain name")
    path: str | None = Field(
        default=None,
        description="Dotfile path to retrieve; if omitted, lists all dotfiles",
    )


class UpdateDomainDotfileRequest(BaseRequestModel):
    """Request to update a domain dotfile."""

    domain: str = Field(description="Domain name")
    path: str = Field(description="Dotfile path")
    data: str = Field(
        max_length=MAXIMUM_DOTFILE_SIZE,
        description="Updated dotfile content",
    )
    permission: DotfilePermission = Field(description="Unix file permission in octal (e.g., '755')")


class DeleteDomainDotfileRequest(BaseRequestModel):
    """Request to delete a domain dotfile."""

    domain: str = Field(description="Domain name")
    path: str = Field(description="Dotfile path to delete")
