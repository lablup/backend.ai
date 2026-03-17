"""
Object Storage DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
    CreateObjectStorageInput,
    DeleteObjectStorageInput,
    GetPresignedDownloadURLInput,
    GetPresignedUploadURLInput,
    ObjectStorageFilter,
    ObjectStorageOrder,
    UpdateObjectStorageInput,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    AdminSearchObjectStoragesPayload,
    BucketsPayload,
    CreateObjectStoragePayload,
    DeleteObjectStoragePayload,
    ObjectStorageNode,
    PresignedDownloadURLPayload,
    PresignedUploadURLPayload,
    UpdateObjectStoragePayload,
)
from ai.backend.common.dto.manager.v2.object_storage.types import (
    ObjectStorageOrderField,
    OrderDirection,
)

__all__ = (
    # Types
    "ObjectStorageOrderField",
    "OrderDirection",
    # Input models (request)
    "AdminSearchObjectStoragesInput",
    "CreateObjectStorageInput",
    "DeleteObjectStorageInput",
    "GetPresignedDownloadURLInput",
    "GetPresignedUploadURLInput",
    "ObjectStorageFilter",
    "ObjectStorageOrder",
    "UpdateObjectStorageInput",
    # Node and Payload models (response)
    "AdminSearchObjectStoragesPayload",
    "BucketsPayload",
    "CreateObjectStoragePayload",
    "DeleteObjectStoragePayload",
    "ObjectStorageNode",
    "PresignedDownloadURLPayload",
    "PresignedUploadURLPayload",
    "UpdateObjectStoragePayload",
)
