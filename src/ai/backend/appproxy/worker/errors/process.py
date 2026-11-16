"""
Process-related exceptions for the worker.
"""

from __future__ import annotations

<<<<<<< HEAD
=======
from typing import override

from aiohttp import web

>>>>>>> f7d925561 (fix(BA-9045): give every AppProxy error class an HTTP status (#17125))
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class SubprocessPipeError(BackendAIError, web.HTTPInternalServerError):
    """Raised when subprocess pipe is not available."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/subprocess-pipe-error"
    error_title = "Subprocess pipe is not available."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )
