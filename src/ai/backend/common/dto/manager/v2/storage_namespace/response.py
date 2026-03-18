"""Response DTOs for Storage Namespace DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminSearchStorageNamespacesPayload",
    "RegisterStorageNamespacePayload",
    "StorageNamespaceNode",
    "UnregisterStorageNamespacePayload",
)


class StorageNamespaceNode(BaseResponseModel):
    """Node model representing a storage namespace."""

    id: UUID = Field(description="Namespace ID")
    storage_id: UUID = Field(description="Parent storage ID")
    namespace: str = Field(description="Namespace bucket or path prefix")


class RegisterStorageNamespacePayload(BaseResponseModel):
    """Payload for storage namespace registration mutation result."""

    namespace: StorageNamespaceNode = Field(description="Registered storage namespace")


class UnregisterStorageNamespacePayload(BaseResponseModel):
    """Payload for storage namespace unregistration mutation result."""

    id: UUID = Field(description="ID of the unregistered storage namespace")


class AdminSearchStorageNamespacesPayload(BaseResponseModel):
    """Payload for storage namespace search result."""

    items: list[StorageNamespaceNode] = Field(description="Storage namespace list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
