from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.common import ObjectNotFound


class AppConfigFragmentConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/app-config-fragment-conflict"
    error_title = (
        "An app config fragment with the same (scope_type, scope_id, name) already exists."
    )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class AppConfigFragmentNotFound(ObjectNotFound):
    object_name = "app config fragment"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
