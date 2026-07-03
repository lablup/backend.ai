"""
Quota-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class QuotaDirectoryNotEmptyError(BackendAIError, web.HTTPConflict):
    """Raised when a quota directory is not empty."""

    error_type = "https://api.backend.ai/probs/storage/quota-directory-not-empty"
    error_title = "Quota Directory Not Empty"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class QuotaScopeNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a quota scope is not found."""

    error_type = "https://api.backend.ai/probs/storage/quota/scope/not-found"
    error_title = "Quota Scope Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class QuotaScopeAlreadyExists(BackendAIError, web.HTTPConflict):
    """Raised when a quota scope already exists."""

    error_type = "https://api.backend.ai/probs/storage/quota/scope/already-exists"
    error_title = "Quota Scope Already Exists"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class InvalidQuotaConfig(BackendAIError, web.HTTPBadRequest):
    """Raised when a quota config is invalid."""

    error_type = "https://api.backend.ai/probs/storage/quota/config/invalid"
    error_title = "Invalid Quota Config"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidQuotaScopeError(BackendAIError, web.HTTPBadRequest):
    """Raised when a quota scope is invalid."""

    error_type = "https://api.backend.ai/probs/storage/quota/scope/invalid"
    error_title = "Invalid Quota Scope"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidQuotaFormatError(BackendAIError, web.HTTPInternalServerError):
    """Raised when quota data has an unexpected format."""

    error_type = "https://api.backend.ai/probs/storage/quota/format/invalid"
    error_title = "Invalid Quota Format"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class QuotaScopeCreationFailedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when creating a quota scope fails."""

    error_type = "https://api.backend.ai/probs/storage/quota/scope/creation-failed"
    error_title = "Quota Scope Creation Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class QuotaTreeNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a quota tree (e.g., XFS project) is not found."""

    error_type = "https://api.backend.ai/probs/storage/quota/tree/not-found"
    error_title = "Quota Tree Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.QUOTA_SCOPE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
