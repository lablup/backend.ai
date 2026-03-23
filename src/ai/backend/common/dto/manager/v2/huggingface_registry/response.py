"""Response DTOs for HuggingFace Registry DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminSearchHuggingFaceRegistriesPayload",
    "CreateHuggingFaceRegistryPayload",
    "DeleteHuggingFaceRegistryPayload",
    "HuggingFaceRegistryNode",
    "UpdateHuggingFaceRegistryPayload",
)


class HuggingFaceRegistryNode(BaseResponseModel):
    """Node model representing a HuggingFace registry."""

    id: UUID = Field(description="Registry ID")
    name: str = Field(description="Registry name")
    url: str = Field(description="HuggingFace Hub URL")
    token: str | None = Field(default=None, description="Access token for the registry")


class CreateHuggingFaceRegistryPayload(BaseResponseModel):
    """Payload for HuggingFace registry creation mutation result."""

    huggingface_registry: HuggingFaceRegistryNode = Field(
        description="Created HuggingFace registry"
    )


class UpdateHuggingFaceRegistryPayload(BaseResponseModel):
    """Payload for HuggingFace registry update mutation result."""

    huggingface_registry: HuggingFaceRegistryNode = Field(
        description="Updated HuggingFace registry"
    )


class DeleteHuggingFaceRegistryPayload(BaseResponseModel):
    """Payload for HuggingFace registry deletion mutation result."""

    id: UUID = Field(description="ID of the deleted HuggingFace registry")


class AdminSearchHuggingFaceRegistriesPayload(BaseResponseModel):
    """Payload for HuggingFace registry search result."""

    items: list[HuggingFaceRegistryNode] = Field(description="HuggingFace registry list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
