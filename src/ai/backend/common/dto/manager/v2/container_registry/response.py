"""
Response DTOs for container registry DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import ContainerRegistryType

__all__ = (
    "ContainerRegistryNode",
    "CreateContainerRegistryPayload",
    "DeleteContainerRegistryPayload",
    "AdminSearchContainerRegistriesPayload",
    "UpdateContainerRegistryPayload",
)


class ContainerRegistryNode(BaseResponseModel):
    """Node model representing a container registry entity. Password is excluded from response."""

    id: UUID = Field(description="Unique identifier of the container registry.")
    url: str = Field(description="URL of the container registry.")
    registry_name: str = Field(description="Unique name identifying the container registry.")
    type: ContainerRegistryType = Field(description="Type of the container registry.")
    project: str | None = Field(
        default=None, description="Project or namespace within the registry."
    )
    username: str | None = Field(
        default=None, description="Username for authenticating with the registry."
    )
    ssl_verify: bool | None = Field(
        default=None, description="Whether SSL certificates are verified."
    )
    is_global: bool | None = Field(
        default=None, description="Whether the registry is accessible globally."
    )
    extra: dict[str, Any] | None = Field(
        default=None, description="Extra metadata or configuration."
    )


class CreateContainerRegistryPayload(BaseResponseModel):
    """Payload for container registry creation mutation result."""

    registry: ContainerRegistryNode = Field(description="Created container registry.")


class UpdateContainerRegistryPayload(BaseResponseModel):
    """Payload for container registry update mutation result."""

    registry: ContainerRegistryNode = Field(description="Updated container registry.")


class DeleteContainerRegistryPayload(BaseResponseModel):
    """Payload for container registry deletion mutation result."""

    id: UUID = Field(description="ID of the deleted container registry.")


class AdminSearchContainerRegistriesPayload(BaseResponseModel):
    """Payload for listing container registries with pagination info."""

    items: list[ContainerRegistryNode] = Field(description="List of container registries.")
    total_count: int = Field(description="Total number of matching registries.")
    has_next_page: bool = Field(description="Whether more items exist after this page.")
    has_previous_page: bool = Field(description="Whether items exist before this page.")
