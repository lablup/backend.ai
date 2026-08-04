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
    "IdleCheckerExclusionTargetMismatch",
    "IdleCheckerNotFound",
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


class IdleCheckerExclusionTargetMismatch(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/idle-checker-exclusion-target-mismatch"
    error_title = "The session is not covered by the given idle checker assignment."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


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
