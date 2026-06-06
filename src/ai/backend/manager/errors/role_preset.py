"""Role preset domain exceptions."""

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


class RolePresetNotFound(ObjectNotFound):
    object_name = "role_preset"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RolePermissionPresetConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-role-permission-preset"
    error_title = "Duplicate role permission preset entry."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
