"""Errors raised by the containerd backend."""

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


class KernelVerbNotSupported(BackendAIError, web.HTTPNotImplemented):
    """Raised when the containerd agent does not support the requested operation."""

    error_type = "https://api.backend.ai/probs/agent/kernel-verb-not-supported"
    error_title = "The containerd agent does not support this operation."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )
