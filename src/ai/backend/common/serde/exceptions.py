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

__all__ = (
    "InvalidFileContent",
    "UnsupportedFileFormat",
)


class UnsupportedFileFormat(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/unsupported-file-format"
    error_title = "The file format is not supported."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidFileContent(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-file-content"
    error_title = "The file content is not readable in its format."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
