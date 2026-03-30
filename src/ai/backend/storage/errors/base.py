"""
Base exception classes for storage proxy.
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


class StorageProxyError(BackendAIError, web.HTTPInternalServerError):
    """Base exception for all storage proxy errors."""

    error_type = "https://api.backend.ai/probs/storage/generic"
    error_title = "Storage Proxy Error"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ProcessExecutionError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a storage operation execution fails."""

    error_type = "https://api.backend.ai/probs/storage/execution/failed"
    error_title = "Storage Operation Execution Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ExternalStorageServiceError(BackendAIError, web.HTTPInternalServerError):
    """Raised when an external storage service operation fails."""

    error_type = "https://api.backend.ai/probs/storage/external/failed"
    error_title = "External Operation Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class NotImplementedAPI(BackendAIError, web.HTTPBadRequest):
    """Raised when an API is not implemented."""

    error_type = "https://api.backend.ai/probs/storage/api/not-implemented"
    error_title = "API Not Implemented"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )
