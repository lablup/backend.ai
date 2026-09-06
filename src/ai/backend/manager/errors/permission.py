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
    "InvalidFieldPermission",
    "InvalidPermissionOperation",
    "NotEnoughPermission",
    "ObjectPermissionNotFound",
    "PermissionNotFound",
    "ReplaceRolePermissionRoleIdMismatch",
    "RoleAlreadyAssigned",
    "RoleNotAssigned",
    "RoleNotFound",
    "UserSystemRoleNotProvisioned",
    "VirtualEntityNotFound",
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


class InvalidPermissionOperation(BackendAIError, web.HTTPBadRequest):
    """An operation with no permission bit — a grant operation — cannot be stored
    as a permission; sharing is judged from entity shares and scope CREATE."""

    error_type = "https://api.backend.ai/probs/invalid-permission-operation"
    error_title = "The operation cannot be stored as a permission."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
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


class VirtualEntityNotFound(BackendAIError, web.HTTPInternalServerError):
    """Raised when a scope's virtual entity is expected to exist but does not.

    A virtual entity is always created alongside any owner scope, so a missing one is
    a server-side data-integrity condition (an invariant violation), not a client
    error — hence 500.
    """

    error_type = "https://api.backend.ai/probs/virtual-entity-not-found"
    error_title = "The virtual entity for the given scope does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
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
