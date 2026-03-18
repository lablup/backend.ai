"""Request DTOs for Reservoir Registry DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AdminSearchReservoirRegistriesInput",
    "CreateReservoirRegistryInput",
    "DeleteReservoirRegistryInput",
    "UpdateReservoirRegistryInput",
)


class CreateReservoirRegistryInput(BaseRequestModel):
    """Input for creating a Reservoir registry."""

    name: str = Field(description="Registry name")
    endpoint: str = Field(description="Reservoir endpoint URL")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    api_version: str = Field(description="API version string")


class UpdateReservoirRegistryInput(BaseRequestModel):
    """Input for updating a Reservoir registry."""

    id: UUID = Field(description="Registry ID to update")
    name: str | None = Field(default=None, description="Updated registry name")
    endpoint: str | None = Field(default=None, description="Updated endpoint URL")
    access_key: str | None = Field(default=None, description="Updated access key")
    secret_key: str | None = Field(default=None, description="Updated secret key")
    api_version: str | None = Field(default=None, description="Updated API version")


class DeleteReservoirRegistryInput(BaseRequestModel):
    """Input for deleting a Reservoir registry."""

    id: UUID = Field(description="Registry ID to delete")


class AdminSearchReservoirRegistriesInput(BaseRequestModel):
    """Input for searching Reservoir registries (admin, no scope)."""

    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")
