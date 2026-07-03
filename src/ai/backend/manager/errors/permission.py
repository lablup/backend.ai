"""Permission and RBAC-related error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

__all__ = (
    "NotEnoughPermission",
    "ObjectPermissionNotFound",
    "PermissionNotFound",
    "ReplaceRolePermissionRoleIdMismatch",
    "RoleAlreadyAssigned",
    "RoleNotAssigned",
    "RoleNotFound",
    "UserSystemRoleNotProvisioned",
)


class RoleNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/role-not-found"
    error_title = "The role does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class UserSystemRoleNotProvisioned(BackendAIError, web.HTTPInternalServerError):
    """Raised when a user is missing the SYSTEM role that should exist for every user.

    This is a server-side data-integrity condition (e.g. legacy or externally
    provisioned accounts) to be remediated via the superadmin ensure-system-role
    API, not a client error.
    """

    error_type = "https://api.backend.ai/probs/user-system-role-not-provisioned"
    error_title = "The user's SYSTEM role is not provisioned."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class RoleAlreadyAssigned(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/role-already-assigned"
    error_title = "The role is already assigned to the user."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class RoleNotAssigned(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/role-not-assigned"
    error_title = "The role is not assigned to the user."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class NotEnoughPermission(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/not-enough-permission"
    error_title = "Insufficient permission to perform this operation."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class PermissionNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/permission-not-found"
    error_title = "The permission does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ObjectPermissionNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/object-permission-not-found"
    error_title = "The object permission does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ReplaceRolePermissionRoleIdMismatch(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/replace-role-permission-role-id-mismatch"
    error_title = "Permission entry role_id does not match the request role_id."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.MISMATCH,
        )
