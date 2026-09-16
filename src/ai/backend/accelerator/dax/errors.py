from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class DAXDeviceNotFound(BackendAIError, web.HTTPNotFound):
    """Raised when a path does not name a dax device known to sysfs."""

    error_type = "https://api.backend.ai/probs/agent/dax-device-not-found"
    error_title = "DAX device not found."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DAXScrubError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a scrub cannot write or verify the device."""

    error_type = "https://api.backend.ai/probs/agent/dax-scrub-failed"
    error_title = "DAX scrub failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
