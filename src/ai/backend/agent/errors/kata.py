"""
KataAgent (Kata Containers backend) operation-related exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class NerdctlError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a ``nerdctl``/containerd subprocess invocation fails."""

    error_type = "https://api.backend.ai/probs/agent/kata/nerdctl-failed"
    error_title = "A nerdctl/containerd subprocess invocation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KataVolumeResolutionError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a Docker named volume cannot be resolved to a host path for
    bind-mounting into a Kata guest."""

    error_type = "https://api.backend.ai/probs/agent/kata/volume-resolution-failed"
    error_title = "Failed to resolve a named volume to a host path."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )
