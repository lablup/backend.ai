"""
Request DTOs for container registry DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel

from .types import ContainerRegistryType

__all__ = (
    "AllowedGroupsInput",
    "CreateContainerRegistryInput",
    "DeleteContainerRegistryInput",
    "UpdateContainerRegistryInput",
)


class AllowedGroupsInput(BaseRequestModel):
    """Input for specifying allowed group membership changes."""

    add: list[str] = Field(
        default_factory=list,
        description="List of group IDs or names to add to the allowed groups.",
    )
    remove: list[str] = Field(
        default_factory=list,
        description="List of group IDs or names to remove from the allowed groups.",
    )


class CreateContainerRegistryInput(BaseRequestModel):
    """Input for creating a new container registry."""

    url: str = Field(description="URL of the container registry.")
    registry_name: str = Field(description="Unique name identifying the container registry.")
    type: ContainerRegistryType = Field(description="Type of the container registry.")
    project: str | None = Field(
        default=None, description="Project or namespace within the registry."
    )
    username: str | None = Field(
        default=None, description="Username for authenticating with the registry."
    )
    password: str | None = Field(
        default=None, description="Password for authenticating with the registry."
    )
    ssl_verify: bool | None = Field(
        default=None, description="Whether to verify SSL certificates when connecting."
    )
    is_global: bool | None = Field(
        default=None, description="Whether the registry is accessible globally."
    )
    extra: dict[str, Any] | None = Field(
        default=None, description="Extra metadata or configuration for the registry."
    )
    allowed_groups: AllowedGroupsInput | None = Field(
        default=None, description="Group membership changes to apply on creation."
    )

    @field_validator("url", mode="before")
    @classmethod
    def url_strip_and_validate(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("url must not be blank")
        return stripped

    @field_validator("registry_name", mode="before")
    @classmethod
    def registry_name_strip_and_validate(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("registry_name must not be blank")
        return stripped


class UpdateContainerRegistryInput(BaseRequestModel):
    """Input for updating an existing container registry. All fields are optional; None means no change."""

    id: UUID = Field(description="Unique identifier of the registry to update.")
    url: str | None = Field(default=None, description="Updated URL of the container registry.")
    registry_name: str | None = Field(
        default=None, description="Updated unique name of the container registry."
    )
    type: ContainerRegistryType | None = Field(
        default=None, description="Updated type of the container registry."
    )
    project: str | None = Field(
        default=None, description="Updated project or namespace within the registry."
    )
    username: str | None = Field(
        default=None, description="Updated username for authenticating with the registry."
    )
    password: str | None = Field(
        default=None, description="Updated password for authenticating with the registry."
    )
    ssl_verify: bool | None = Field(default=None, description="Updated SSL verification setting.")
    is_global: bool | None = Field(
        default=None, description="Updated global accessibility setting."
    )
    extra: dict[str, Any] | None = Field(
        default=None, description="Updated extra metadata or configuration."
    )
    allowed_groups: AllowedGroupsInput | None = Field(
        default=None, description="Group membership changes to apply on update."
    )

    @field_validator("url", mode="before")
    @classmethod
    def url_strip_and_validate(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("url must not be blank")
        return stripped

    @field_validator("registry_name", mode="before")
    @classmethod
    def registry_name_strip_and_validate(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("registry_name must not be blank")
        return stripped


class DeleteContainerRegistryInput(BaseRequestModel):
    """Input for deleting a container registry."""

    id: UUID = Field(description="Unique identifier of the registry to delete.")
