"""
Authentication and user-related exceptions.
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

from .common import ObjectNotFound


class InvalidCredentials(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-credentials"
    error_title = "Invalid credentials for authentication."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InsufficientPrivilege(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/insufficient-privilege"
    error_title = "Insufficient privilege."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InvalidAuthParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-auth-params"
    error_title = "Missing or invalid authorization parameters."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AuthorizationFailed(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/auth-failed"
    error_title = "Credential/signature mismatch."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class PasswordExpired(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/password-expired"
    error_title = "Password has expired."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.DATA_EXPIRED,
        )


class EmailAlreadyExistsError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/email-already-exists"
    error_title = "Email already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class UserCreationError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-creation-failed"
    error_title = "Failed to create user account."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UserNotFound(ObjectNotFound):
    object_name = "user"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GroupMembershipNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/group-membership-not-found"
    error_title = "User is not a member of the specified group."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
