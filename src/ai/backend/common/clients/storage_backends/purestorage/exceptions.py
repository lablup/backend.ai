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


class UnauthorizedPurityClient(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/purity-unauthorized-client"
    error_title = "Unauthorized Purity Client"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class PureStorageCommandFailedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/purestorage/command-failed"
    error_title = "PureStorage Command Failed"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class PureStorageStdoutNotAvailableError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/purestorage/stdout-unavailable"
    error_title = "PureStorage Command Stdout Not Available"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class RapidFileToolkitVersionNotDetectedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/storage/purestorage/toolkit-version-not-detected"
    error_title = "RapidFile Toolkit Version Not Detected"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_READY,
        )
