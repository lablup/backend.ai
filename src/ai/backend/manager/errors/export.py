"""Export-related exceptions."""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ExportReportNotFound(BackendAIError, web.HTTPNotFound):
    """Raised when requested export report is not found."""

    error_type = "https://api.backend.ai/probs/export-report-not-found"
    error_title = "Export report not found."

    def __init__(self, report_key: str) -> None:
        super().__init__(extra_msg=f"Unknown report: {report_key}")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidExportFieldKeys(BackendAIError, web.HTTPBadRequest):
    """Raised when requested field keys are invalid."""

    error_type = "https://api.backend.ai/probs/invalid-export-field-keys"
    error_title = "Invalid export field keys."

    def __init__(self, invalid_keys: list[str]) -> None:
        super().__init__(extra_msg=f"Invalid field keys: {invalid_keys}")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class TooManyConcurrentExports(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when concurrent export limit is exceeded."""

    error_type = "https://api.backend.ai/probs/too-many-concurrent-exports"
    error_title = "Too many concurrent exports."

    def __init__(self) -> None:
        super().__init__(extra_msg="Too many concurrent export requests. Please try again later.")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
