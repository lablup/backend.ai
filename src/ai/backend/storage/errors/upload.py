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


class TusSessionNotFoundError(BackendAIError, web.HTTPNotFound):
    """
    Raised when a TUS handler is invoked for a session that is not registered
    in Valkey (never created, or its state expired by TTL).
    """

    error_type = "https://api.backend.ai/probs/storage/no-such-upload-session"
    error_title = "No such upload session"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
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


class _ChecksumMismatch(web.HTTPClientError):
    """
    TUS Checksum extension defines HTTP 460 for checksum mismatches.
    aiohttp does not ship a built-in class for this code, so we declare one.
    """

    status_code = 460


class ChunkChecksumMismatchError(BackendAIError, _ChecksumMismatch):
    """
    Raised when ``Upload-Checksum`` header does not match the SHA-256 digest
    of the received chunk body (HTTP 460 per TUS Checksum extension).
    """

    error_type = "https://api.backend.ai/probs/storage/chunk-checksum-mismatch"
    error_title = "Upload Chunk Checksum Mismatch"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidUploadChecksumHeaderError(BackendAIError, web.HTTPBadRequest):
    """
    Raised when ``Upload-Checksum`` header is malformed or specifies an
    unsupported algorithm (only ``sha256`` is accepted).
    """

    error_type = "https://api.backend.ai/probs/storage/invalid-upload-checksum"
    error_title = "Invalid Upload-Checksum header"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
