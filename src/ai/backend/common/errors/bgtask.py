from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class BgtaskNotRegisteredError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/bgtask-not-registered"
    error_title = "Background Task Not Registered"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class BgtaskNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/bgtask-not-found"
    error_title = "Background Task Not Found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class BgtaskFailedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/bgtask-failed"
    error_title = "Background Task Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class BgtaskCancelledError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/bgtask-cancelled"
    error_title = "Background Task Cancelled"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.CANCELED,
        )
