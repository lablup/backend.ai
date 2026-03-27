"""Storage Namespace DTOs v2 for Manager API."""

from ai.backend.common.dto.manager.v2.storage_namespace.request import (
    AdminSearchStorageNamespacesInput,
    RegisterStorageNamespaceInput,
    UnregisterStorageNamespaceInput,
)
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    AdminSearchStorageNamespacesPayload,
    RegisterStorageNamespacePayload,
    StorageNamespaceNode,
    UnregisterStorageNamespacePayload,
)

__all__ = (
    "AdminSearchStorageNamespacesInput",
    "AdminSearchStorageNamespacesPayload",
    "RegisterStorageNamespaceInput",
    "RegisterStorageNamespacePayload",
    "StorageNamespaceNode",
    "UnregisterStorageNamespaceInput",
    "UnregisterStorageNamespacePayload",
)
