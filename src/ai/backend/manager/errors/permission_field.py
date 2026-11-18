"""Permission field error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.permission import PermissionFieldType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode, FieldNotFoundError

__all__ = (
    "InvalidFieldPermission",
    "InvalidPermissionOperation",
    "PermissionAlreadyGranted",
    "PermissionNotFound",
    "ReplaceRolePermissionRoleIdMismatch",
)


class PermissionNotFound(FieldNotFoundError):
    error_type = "https://api.backend.ai/probs/permission-not-found"
    error_title = "The permission entry does not exist."

    def __init__(
        self,
        extra_msg: str | None = None,
        *,
        operation: ActionOperationType = ActionOperationType.GET,
    ) -> None:
        super().__init__(extra_msg, field_type=PermissionFieldType(), operation=operation)


class PermissionAlreadyGranted(FieldError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/permission-already-granted"
    error_title = "The role already holds the permission."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            PermissionFieldType(), ActionOperationType.CREATE, ErrorDetail.ALREADY_EXISTS
        )


class InvalidFieldPermission(BackendAIError, web.HTTPBadRequest):
    """A field scope the ops refuse: a malformed path, a bit outside READ|UPDATE,
    or a bit stated both on every field and on a path."""

    error_type = "https://api.backend.ai/probs/invalid-field-permission"
    error_title = "The field scope is invalid."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidPermissionOperation(FieldError, web.HTTPBadRequest):
    """An operation with no permission bit — a grant operation — cannot be stored
    as a permission; sharing is judged from entity shares and scope CREATE."""

    error_type = "https://api.backend.ai/probs/invalid-permission-operation"
    error_title = "The operation cannot be stored as a permission."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            PermissionFieldType(), ActionOperationType.CREATE, ErrorDetail.INVALID_PARAMETERS
        )


class ReplaceRolePermissionRoleIdMismatch(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/replace-role-permission-role-id-mismatch"
    error_title = "Permission entry role_id does not match the request role_id."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            PermissionFieldType(), ActionOperationType.UPDATE, ErrorDetail.MISMATCH
        )
