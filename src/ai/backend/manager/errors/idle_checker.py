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
from ai.backend.manager.errors.common import ObjectNotFound

__all__ = (
    "IdleCheckerAssignmentAlreadyExists",
    "IdleCheckerAssignmentNotFound",
    "IdleCheckerAssignmentScopeNotFound",
    "IdleCheckerNotFound",
    "InvalidIdleCheckerAssignmentScopeId",
)


class IdleCheckerNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/idle-checker-not-found"
    object_name = "idle checker"


class IdleCheckerAssignmentNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/idle-checker-assignment-not-found"
    object_name = "idle checker assignment"


class IdleCheckerAssignmentScopeNotFound(ObjectNotFound):
    error_type = "https://api.backend.ai/probs/idle-checker-assignment-scope-not-found"
    object_name = "idle checker assignment scope"


class IdleCheckerAssignmentAlreadyExists(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/idle-checker-assignment-already-exists"
    error_title = "The idle checker is already assigned to the given scope."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class InvalidIdleCheckerAssignmentScopeId(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-idle-checker-assignment-scope-id"
    error_title = "The scope identifier must be a UUID."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
