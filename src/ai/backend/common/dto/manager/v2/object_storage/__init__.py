"""
Object Storage DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.object_storage.request import (
    CreateObjectStorageInput,
    DeleteObjectStorageInput,
    GetPresignedDownloadURLInput,
    GetPresignedUploadURLInput,
    UpdateObjectStorageInput,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
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
    "CreateObjectStorageInput",
    "DeleteObjectStorageInput",
    "GetPresignedDownloadURLInput",
    "GetPresignedUploadURLInput",
    "UpdateObjectStorageInput",
    # Node and Payload models (response)
    "BucketsPayload",
    "CreateObjectStoragePayload",
    "DeleteObjectStoragePayload",
    "ObjectStorageNode",
    "PresignedDownloadURLPayload",
    "PresignedUploadURLPayload",
    "UpdateObjectStoragePayload",
)
