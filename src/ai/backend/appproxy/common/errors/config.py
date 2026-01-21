"""Configuration validation errors for App Proxy."""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ConfigValidationError(BackendAIError):
    """Base class for configuration validation errors."""

    error_type = "https://api.backend.ai/probs/appproxy/config-validation-error"
    error_title = "Configuration validation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidUIDTypeError(BackendAIError):
    """Raised when UID type is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy/invalid-uid-type"
    error_title = "UID must be an integer or string."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class UserNotFoundError(BackendAIError):
    """Raised when specified user is not found in system."""

    error_type = "https://api.backend.ai/probs/appproxy/user-not-found"
    error_title = "Specified user not found in system."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidGIDTypeError(BackendAIError):
    """Raised when GID type is invalid."""

    error_type = "https://api.backend.ai/probs/appproxy/invalid-gid-type"
    error_title = "GID must be an integer or string."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class GroupNotFoundError(BackendAIError):
    """Raised when specified group is not found in system."""

    error_type = "https://api.backend.ai/probs/appproxy/group-not-found"
    error_title = "Specified group not found in system."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingAnnotationError(BackendAIError):
    """Raised when field annotation is missing."""

    error_type = "https://api.backend.ai/probs/appproxy/missing-annotation"
    error_title = "Field annotation is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
