from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.common import ObjectNotFound


class EntityInvitationNotFound(ObjectNotFound):
    object_name = "entity-invitation"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_INVITATION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DuplicateEntityInvitationError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-entity-invitation"
    error_title = "Duplicate entity invitation."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_INVITATION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class EntityInvitationInvalidStatus(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/entity-invitation-invalid-status"
    error_title = "Invalid entity invitation status transition."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENTITY_INVITATION,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
