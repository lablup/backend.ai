from typing import override

from aiohttp import web

from ai.backend.common.data.entity.keypair import KeyPairFieldType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode


class UserNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/user-not-found"
    error_title = "The user does not exist."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(UserEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class UserPurgeInProgress(EntityError, web.HTTPConflict):
    """Raised when a write names a user a purge is working through."""

    error_type = "https://api.backend.ai/probs/user-purge-in-progress"
    error_title = "User is being purged."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(UserEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT)


class UserConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/user-conflict"
    error_title = "The user already exists."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(UserEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT)


class UserModificationBadRequest(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/user-modification-bad-request"
    error_title = "Failed to modify user due to bad request."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            UserEntityType(), ActionOperationType.UPDATE, ErrorDetail.BAD_REQUEST
        )


class UserCreationBadRequest(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/user-creation-bad-request"
    error_title = "Failed to create user due to bad request."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            UserEntityType(), ActionOperationType.CREATE, ErrorDetail.BAD_REQUEST
        )


class UserCreationFailure(EntityError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-creation-failure"
    error_title = "Failed to create user."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            UserEntityType(), ActionOperationType.CREATE, ErrorDetail.INTERNAL_ERROR
        )


class UserModificationFailure(EntityError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-modification-failure"
    error_title = "Failed to modify user."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            UserEntityType(), ActionOperationType.UPDATE, ErrorDetail.INTERNAL_ERROR
        )


class UserPurgeFailure(EntityError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/user-purge-failure"
    error_title = "Failed to purge user."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            UserEntityType(), ActionOperationType.PURGE, ErrorDetail.INTERNAL_ERROR
        )


class KeyPairNotFound(FieldError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/keypair-not-found"
    error_title = "The key pair does not exist."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(KeyPairFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class KeyPairForbidden(FieldError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/keypair-forbidden"
    error_title = "The key pair is not allowed to be used."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(KeyPairFieldType(), ActionOperationType.GET, ErrorDetail.FORBIDDEN)
