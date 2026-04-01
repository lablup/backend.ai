"""
DTOs for the object-storage domain (Client SDK ↔ Manager).

Re-exports request/response models so callers can do::

    from ai.backend.common.dto.manager.object_storage import (
        GetPresignedUploadURLReq,
        ObjectStorageListResponse,
    )
"""

from __future__ import annotations

from .request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
)
from .response import (
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
    ObjectStorageResponse,
)

__all__ = (
    # Request models
    "GetPresignedUploadURLReq",
    "GetPresignedDownloadURLReq",
    # Response models
    "ObjectStorageResponse",
    "ObjectStorageListResponse",
    "ObjectStorageBucketsResponse",
    "ObjectStorageAllBucketsResponse",
)
