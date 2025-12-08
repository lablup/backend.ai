"""
Common/shared exceptions for storage proxy.
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


class InvalidAPIParameters(BackendAIError, web.HTTPBadRequest):
    """Raised when API parameters are invalid."""

    error_type = "https://api.backend.ai/probs/storage/invalid-api-params"
    error_title = "Invalid API parameters"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class StorageNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a storage config is not found."""

    error_type = "https://api.backend.ai/probs/storage/object-not-found"
    error_title = "Storage Config Not Found"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class StorageTypeInvalidError(BackendAIError, web.HTTPBadRequest):
    """Raised when a storage type is invalid."""

    error_type = "https://api.backend.ai/probs/storage/object-type-invalid"
    error_title = "Storage Config Invalid Type"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class StorageTransferError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a storage transfer operation fails."""

    error_type = "https://api.backend.ai/probs/storage/transfer/failed"
    error_title = "Storage Transfer Failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class StorageStepRequiredStepNotProvided(BackendAIError, web.HTTPBadRequest):
    """Raised when a required storage step mapping is not provided."""

    error_type = "https://api.backend.ai/probs/storage/step-mapping-not-provided"
    error_title = "Storage Step Mapping Not Provided"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


# Path validation exceptions


class InvalidPathError(BackendAIError, web.HTTPBadRequest):
    """Raised when a path is invalid (empty, contains invalid characters, or attempts traversal)."""

    error_type = "https://api.backend.ai/probs/storage/path/invalid"
    error_title = "Invalid Path"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidSocketPathError(BackendAIError, web.HTTPBadRequest):
    """Raised when a socket path is invalid or not provided."""

    error_type = "https://api.backend.ai/probs/storage/socket-path/invalid"
    error_title = "Invalid Socket Path"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidConfigurationSourceError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a configuration source is invalid."""

    error_type = "https://api.backend.ai/probs/storage/config/invalid-source"
    error_title = "Invalid Configuration Source"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidDataLengthError(BackendAIError, web.HTTPBadRequest):
    """Raised when data has an invalid length."""

    error_type = "https://api.backend.ai/probs/storage/data/invalid-length"
    error_title = "Invalid Data Length"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ServiceNotInitializedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a service is not properly initialized."""

    error_type = "https://api.backend.ai/probs/storage/service/not-initialized"
    error_title = "Service Not Initialized"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_PROXY,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_READY,
        )
