"""
Request DTOs for container registry DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    ContainerRegistryOrderField,
    ContainerRegistryType,
    ContainerRegistryTypeFilter,
    OrderDirection,
)

__all__ = (
    "AllowedGroupsInput",
    "ContainerRegistryFilter",
    "ContainerRegistryOrder",
    "CreateContainerRegistryInput",
    "DeleteContainerRegistryInput",
    "AdminSearchContainerRegistriesInput",
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


class ContainerRegistryFilter(BaseRequestModel):
    """Filter conditions for container registry search."""

    registry_name: StringFilter | None = Field(default=None, description="Filter by registry name.")
    type: ContainerRegistryTypeFilter | None = Field(
        default=None, description="Filter by registry type."
    )
    is_global: bool | None = Field(default=None, description="Filter by global accessibility.")


class ContainerRegistryOrder(BaseRequestModel):
    """Order specification for container registry search."""

    field: ContainerRegistryOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchContainerRegistriesInput(BaseRequestModel):
    """Input for searching container registries with filters, orders, and pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: ContainerRegistryFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ContainerRegistryOrder] | None = Field(
        default=None, description="Order specifications."
    )
    # Cursor-based pagination (Relay)
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    # Offset-based pagination
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")
