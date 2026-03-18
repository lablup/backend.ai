"""Response DTOs for Reservoir Registry DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminSearchReservoirRegistriesPayload",
    "CreateReservoirRegistryPayload",
    "DeleteReservoirRegistryPayload",
    "ReservoirRegistryNode",
    "UpdateReservoirRegistryPayload",
)


class ReservoirRegistryNode(BaseResponseModel):
    """Node model representing a Reservoir registry."""

    id: UUID = Field(description="Registry ID")
    name: str = Field(description="Registry name")
    endpoint: str = Field(description="Reservoir endpoint URL")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    api_version: str = Field(description="API version string")


class CreateReservoirRegistryPayload(BaseResponseModel):
    """Payload for Reservoir registry creation mutation result."""

    registry: ReservoirRegistryNode = Field(description="Created Reservoir registry")


class UpdateReservoirRegistryPayload(BaseResponseModel):
    """Payload for Reservoir registry update mutation result."""

    registry: ReservoirRegistryNode = Field(description="Updated Reservoir registry")


class DeleteReservoirRegistryPayload(BaseResponseModel):
    """Payload for Reservoir registry deletion mutation result."""

    id: UUID = Field(description="ID of the deleted Reservoir registry")


class AdminSearchReservoirRegistriesPayload(BaseResponseModel):
    """Payload for Reservoir registry search result."""

    items: list[ReservoirRegistryNode] = Field(description="Reservoir registry list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
