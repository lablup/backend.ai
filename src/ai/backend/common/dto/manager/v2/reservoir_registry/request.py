"""Request DTOs for Reservoir Registry DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import NonEmptyList

__all__ = (
    "AdminSearchReservoirRegistriesInput",
    "CreateReservoirRegistryInput",
    "DeleteReservoirRegistryInput",
    "PartialBulkPurgeReservoirRegistriesInput",
    "PartialBulkUpdateReservoirRegistriesInput",
    "PartialBulkUpdateReservoirRegistryItemInput",
    "UpdateReservoirRegistryBody",
    "UpdateReservoirRegistryInput",
)


class CreateReservoirRegistryInput(BaseRequestModel):
    """Input for creating a Reservoir registry."""

    name: str = Field(description="Registry name")
    endpoint: str = Field(description="Reservoir endpoint URL")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    api_version: str = Field(description="API version string")


class UpdateReservoirRegistryBody(BaseRequestModel):
    """Fields to update on a Reservoir registry."""

    name: str | None = Field(default=None, description="Updated registry name")
    endpoint: str | None = Field(default=None, description="Updated endpoint URL")
    access_key: str | None = Field(default=None, description="Updated access key")
    secret_key: str | None = Field(default=None, description="Updated secret key")
    api_version: str | None = Field(default=None, description="Updated API version")


class UpdateReservoirRegistryInput(UpdateReservoirRegistryBody):
    """Input for updating a Reservoir registry."""

    id: UUID = Field(description="Registry ID to update")


class DeleteReservoirRegistryInput(BaseRequestModel):
    """Input for deleting a Reservoir registry."""

    id: UUID = Field(description="Registry ID to delete")


class PartialBulkUpdateReservoirRegistryItemInput(BaseRequestModel):
    """One Reservoir registry of a partial bulk update and the fields to update on it."""

    id: UUID = Field(description="ID of the registry to update.")
    input: UpdateReservoirRegistryBody = Field(description="Fields to update on the registry.")


class PartialBulkUpdateReservoirRegistriesInput(BaseRequestModel):
    """Input for updating several Reservoir registries, each answered for separately."""

    items: NonEmptyList[PartialBulkUpdateReservoirRegistryItemInput] = Field(
        description="The registries to update, each with its fields."
    )


class PartialBulkPurgeReservoirRegistriesInput(BaseRequestModel):
    """Input for purging several Reservoir registries, each answered for separately."""

    ids: NonEmptyList[UUID] = Field(description="IDs of the registries to purge.")


class AdminSearchReservoirRegistriesInput(BaseRequestModel):
    """Input for searching Reservoir registries (admin, no scope)."""

    first: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items after cursor"
    )
    after: str | None = Field(default=None, description="Cursor-based: start cursor (exclusive)")
    last: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items before cursor"
    )
    before: str | None = Field(default=None, description="Cursor-based: end cursor (exclusive)")
    limit: int | None = Field(default=None, ge=1, description="Offset-based: max results per page")
    offset: int | None = Field(default=None, ge=0, description="Offset-based: pagination offset")
