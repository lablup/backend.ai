from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.common import ObjectNotFound


class RoleInvitationNotFound(ObjectNotFound):
    object_name = "role-invitation"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE_INVITATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DuplicateRoleInvitationError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-role-invitation"
    error_title = "Duplicate role invitation."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE_INVITATION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class RoleInvitationInvalidState(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/role-invitation-invalid-state"
    error_title = "Invalid role invitation state transition."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE_INVITATION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
