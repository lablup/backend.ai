"""
Storage DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.storage.request import (
    GetVFSStorageInput,
    ListVFSStorageInput,
    VFSDownloadFileInput,
    VFSListFilesInput,
)
from ai.backend.common.dto.manager.v2.storage.response import (
    GetVFSStoragePayload,
    ListVFSStoragePayload,
    VFSStorageNode,
)
from ai.backend.common.dto.manager.v2.storage.types import (
    OrderDirection,
    StorageOrderField,
)

__all__ = (
    # Types
    "OrderDirection",
    "StorageOrderField",
    # Input models (request)
    "GetVFSStorageInput",
    "ListVFSStorageInput",
    "VFSDownloadFileInput",
    "VFSListFilesInput",
    # Node and Payload models (response)
    "GetVFSStoragePayload",
    "ListVFSStoragePayload",
    "VFSStorageNode",
)
