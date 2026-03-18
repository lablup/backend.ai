"""Request DTOs for HuggingFace Registry DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AdminSearchHuggingFaceRegistriesInput",
    "CreateHuggingFaceRegistryInput",
    "DeleteHuggingFaceRegistryInput",
    "UpdateHuggingFaceRegistryInput",
)


class CreateHuggingFaceRegistryInput(BaseRequestModel):
    """Input for creating a HuggingFace registry."""

    name: str = Field(description="Registry name")
    url: str = Field(description="HuggingFace Hub URL")
    token: str | None = Field(default=None, description="Access token for the registry")


class UpdateHuggingFaceRegistryInput(BaseRequestModel):
    """Input for updating a HuggingFace registry."""

    id: UUID = Field(description="Registry ID to update")
    name: str | None = Field(default=None, description="Updated registry name")
    url: str | None = Field(default=None, description="Updated HuggingFace Hub URL")
    token: str | None = Field(default=None, description="Updated access token")


class DeleteHuggingFaceRegistryInput(BaseRequestModel):
    """Input for deleting a HuggingFace registry."""

    id: UUID = Field(description="Registry ID to delete")


class AdminSearchHuggingFaceRegistriesInput(BaseRequestModel):
    """Input for searching HuggingFace registries (admin, no scope)."""

    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")
