"""
Volume-related exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidVolumeError(BackendAIError, web.HTTPBadRequest):
    """Raised when a volume is invalid."""

    error_type = "https://api.backend.ai/probs/storage/volume/invalid"
    error_title = "Invalid Volume"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class VolumeNotInitializedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a volume is not properly initialized."""

    error_type = "https://api.backend.ai/probs/storage/volume/not-initialized"
    error_title = "Volume Not Initialized"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_READY,
        )


class MetadataTooLargeError(BackendAIError, web.HTTPBadRequest):
    """Raised when metadata exceeds the size limit."""

    error_type = "https://api.backend.ai/probs/storage/volume/metadata-too-large"
    error_title = "Metadata Too Large"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
