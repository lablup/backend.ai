"""Role preset domain exceptions."""

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

from .common import ObjectNotFound


class RolePresetNotFound(ObjectNotFound):
    object_name = "role_preset"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidRoleNameTemplate(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-role-name-template"
    error_title = "Invalid role name template."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class SystemRoleNotEditable(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/system-role-not-editable"
    error_title = "A SYSTEM role cannot be purged; edit the role preset instead."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class RolePermissionPresetConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-role-permission-preset"
    error_title = "Duplicate role permission preset entry."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
