"""
Authentication and user-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.keypair import KeyPairFieldType
from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.common.data.entity.login_session import LoginSessionFieldType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode

from .common import ObjectNotFound


class InvalidCredentials(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-credentials"
    error_title = "Invalid credentials for authentication."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InsufficientPrivilege(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/insufficient-privilege"
    error_title = "Insufficient privilege."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InvalidAuthParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-auth-params"
    error_title = "Missing or invalid authorization parameters."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AuthorizationFailed(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/auth-failed"
    error_title = "Credential/signature mismatch."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class OpenIDAuthenticationFailed(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/openid-not-authenticated"
    error_title = "Not authenticated by OpenID Provider"

    def __init__(self) -> None:
        # Legacy reason phrase, kept for clients that already read it.
        super().__init__(reason=self.error_title)

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class PasswordExpired(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/password-expired"
    error_title = "Password has expired."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.DATA_EXPIRED,
        )


class EmailAlreadyExistsError(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/email-already-exists"
    error_title = "Email already exists."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            UserEntityType(), ActionOperationType.CREATE, ErrorDetail.ALREADY_EXISTS
        )


class UserCreationError(EntityError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-creation-failed"
    error_title = "Failed to create user account."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            UserEntityType(), ActionOperationType.CREATE, ErrorDetail.INTERNAL_ERROR
        )


class UserNotFound(EntityError, ObjectNotFound):
    object_name = "user"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(UserEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class AccessKeyNotFound(FieldError, ObjectNotFound):
    object_name = "access key"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(KeyPairFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class GroupMembershipNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/group-membership-not-found"
    error_title = "User is not a member of the specified group."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidClientIPConfig(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/invalid-client-ip-config"
    error_title = "Invalid client IP configuration."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class LoginSessionNotFoundError(FieldError, ObjectNotFound):
    object_name = "login_session"

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            LoginSessionFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class LoginSessionExpiredError(BackendAIError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/login-session-expired"
    error_title = "Login session has expired."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AUTH,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.DATA_EXPIRED,
        )


class LoginBlockedError(BackendAIError, web.HTTPTooManyRequests):
    error_type = "https://api.backend.ai/probs/login-blocked"
    error_title = "Too many failed login attempts."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AUTH,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class LoginClientTypeNotFound(EntityError, ObjectNotFound):
    object_name = "login_client_type"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            LoginClientTypeEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class LoginClientTypeConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/login-client-type-conflict"
    error_title = "A login client type with the same name already exists."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            LoginClientTypeEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class TooManyConcurrentLoginSessions(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/active-login-session-exists"
    error_title = "Too many concurrent login sessions for this user."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AUTH,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.CONFLICT,
        )
