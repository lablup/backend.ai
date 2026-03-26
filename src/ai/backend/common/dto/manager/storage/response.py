"""
Response DTOs for storage domain.

Covers object storage and VFS storage response models.

Models already defined in ``common.dto.manager.response`` are re-exported here
so that callers can import everything from a single domain-specific path.

Note on VFS models: ``VFSStorage``, ``GetVFSStorageResponse``, and
``ListVFSStorageResponse`` are defined here (in ``common``) as the canonical
location, because ``common`` cannot import from ``manager``.
``manager.dto.response`` re-exports these models for backward compatibility.
"""

from pydantic import BaseModel

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.response import (
    GetPresignedDownloadURLResponse,
    GetPresignedUploadURLResponse,
    ObjectStorageAllBucketsResponse,
    ObjectStorageBucketsResponse,
    ObjectStorageListResponse,
    ObjectStorageResponse,
)

__all__ = (
    # Object storage models (re-exported from common.dto.manager.response)
    "ObjectStorageResponse",
    "ObjectStorageListResponse",
    # Presigned URL models (re-exported from common.dto.manager.response)
    "GetPresignedDownloadURLResponse",
    "GetPresignedUploadURLResponse",
    # Object storage bucket models (re-exported from common.dto.manager.response)
    "ObjectStorageBucketsResponse",
    "ObjectStorageAllBucketsResponse",
    # VFS storage models (canonical location; re-exported by manager.dto.response)
    "VFSStorage",
    "GetVFSStorageResponse",
    "ListVFSStorageResponse",
)


# ---------------------------------------------------------------------------
# VFS storage models
#
# These are the canonical definitions.  They live in ``common`` because the
# ``common → manager`` dependency direction forbids importing from ``manager``.
# ``ai.backend.manager.dto.response`` re-exports them for callers that already
# import from the manager package.
# ---------------------------------------------------------------------------


class VFSStorage(BaseModel):
    name: str
    base_path: str
    host: str


class GetVFSStorageResponse(BaseResponseModel):
    storage: VFSStorage


class ListVFSStorageResponse(BaseResponseModel):
    storages: list[VFSStorage]
