"""Request DTOs for Storage Namespace DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AdminSearchStorageNamespacesInput",
    "RegisterStorageNamespaceInput",
    "UnregisterStorageNamespaceInput",
)


class RegisterStorageNamespaceInput(BaseRequestModel):
    """Input for registering a storage namespace."""

    storage_id: UUID = Field(description="Storage ID to register namespace for")
    namespace: str = Field(description="Namespace bucket or path prefix")


class UnregisterStorageNamespaceInput(BaseRequestModel):
    """Input for unregistering a storage namespace."""

    storage_id: UUID = Field(description="Storage ID of the namespace to unregister")
    namespace: str = Field(description="Namespace bucket or path prefix to unregister")


class AdminSearchStorageNamespacesInput(BaseRequestModel):
    """Input for searching storage namespaces (admin, no scope)."""

    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")
