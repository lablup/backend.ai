"""Role error definitions."""

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode

__all__ = (
    "InvalidRoleSeed",
    "RoleAlreadyAssigned",
    "RoleNotAssigned",
    "RoleNotFound",
)


class RoleNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/role-not-found"
    error_title = "The role does not exist."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(RoleEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


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


class InvalidRoleSeed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-role-seed"
    error_title = "The seed role declaration is not valid."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROLE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
