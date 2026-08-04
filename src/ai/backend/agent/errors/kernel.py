"""
Kernel and runner-related exceptions for the agent.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.kernel_runner.errors import (
    OutputQueueMismatchError,
    OutputQueueNotInitializedError,
    RunIdNotSetError,
)

__all__ = [
    "AsyncioContextError",
    "KernelRunnerNotInitializedError",
    "OutputQueueMismatchError",
    "OutputQueueNotInitializedError",
    "RunIdNotSetError",
]

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class KernelRunnerNotInitializedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the kernel runner is not initialized when it should be."""

    error_type = "https://api.backend.ai/probs/agent/kernel-runner-not-initialized"
    error_title = "Kernel runner is not initialized."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_READY,
        )


class AsyncioContextError(BackendAIError, web.HTTPInternalServerError):
    """Raised when asyncio context is invalid or unavailable."""

    error_type = "https://api.backend.ai/probs/agent/asyncio-context-error"
    error_title = "Asyncio context is invalid or unavailable."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )


class SubprocessStreamError(BackendAIError, web.HTTPInternalServerError):
    """Raised when subprocess stdin/stdout stream is not available."""

    error_type = "https://api.backend.ai/probs/agent/subprocess-stream-error"
    error_title = "Subprocess stream is not available."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )



