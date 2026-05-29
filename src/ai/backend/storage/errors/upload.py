"""
Upload session related exceptions.
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


class ChunkConflictError(BackendAIError, web.HTTPConflict):
    """
    Raised when an incoming chunk targets an offset that already holds a
    different chunk in the upload session (409 Conflict).
    """

    error_type = "https://api.backend.ai/probs/storage/chunk-conflict"
    error_title = "Upload Chunk Conflict"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class UploadChunkExceedsTotalSizeError(BackendAIError, web.HTTPConflict):
    """
    Raised when a PATCH chunk's offset+length would write past the declared
    ``Upload-Length`` (409 Conflict). The Upload-Offset header itself is in
    range; the chunk's body simply overruns the remaining slot.
    """

    error_type = "https://api.backend.ai/probs/storage/upload-chunk-exceeds-total-size"
    error_title = "Upload Chunk Exceeds Total Size"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class UploadSessionCorruptedError(BackendAIError, web.HTTPInternalServerError):
    """
    Raised when the upload session metadata stored in Valkey cannot be parsed,
    is structurally invalid, or has gone missing at a stage that requires it.
    """

    error_type = "https://api.backend.ai/probs/storage/upload-session-corrupted"
    error_title = "Upload Session Corrupted"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
