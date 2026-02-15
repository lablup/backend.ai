"""
Response DTOs for the object-storage domain.

Models are re-exported from ``common.dto.manager.response`` so that
the client SDK can import from a single domain-specific path.
"""

from ai.backend.common.dto.manager.response import (
    GetPresignedDownloadURLResponse as GetPresignedDownloadURLResponse,
)
from ai.backend.common.dto.manager.response import (
    GetPresignedUploadURLResponse as GetPresignedUploadURLResponse,
)
from ai.backend.common.dto.manager.response import (
    ObjectStorageAllBucketsResponse as ObjectStorageAllBucketsResponse,
)
from ai.backend.common.dto.manager.response import (
    ObjectStorageBucketsResponse as ObjectStorageBucketsResponse,
)
from ai.backend.common.dto.manager.response import (
    ObjectStorageListResponse as ObjectStorageListResponse,
)
from ai.backend.common.dto.manager.response import (
    ObjectStorageResponse as ObjectStorageResponse,
)
