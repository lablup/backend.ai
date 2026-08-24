"""Entity label domain exceptions."""

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


class LabelNotFound(ObjectNotFound):
    object_name = "label"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.LABEL,
            operation=ErrorOperation.HARD_DELETE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class LabelConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-label"
    error_title = "The entity already carries this label."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.LABEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
