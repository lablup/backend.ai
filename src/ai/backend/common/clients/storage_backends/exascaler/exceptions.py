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


class EXAScalerCommandFailedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/ddn/command-failed"
    error_title = "DDN Command Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class EXAScalerCommandStdoutNotAvailableError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/subprocess/stdout-unavailable"
    error_title = "Subprocess Stdout Not Available"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
