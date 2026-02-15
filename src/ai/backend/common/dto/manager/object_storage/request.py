"""
Request DTOs for the object-storage domain.

Models are re-exported from ``common.dto.manager.request`` so that
the client SDK can import from a single domain-specific path.
"""

from ai.backend.common.dto.manager.request import (
    GetPresignedDownloadURLReq as GetPresignedDownloadURLReq,
)
from ai.backend.common.dto.manager.request import (
    GetPresignedUploadURLReq as GetPresignedUploadURLReq,
)
