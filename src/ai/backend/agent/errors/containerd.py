"""Errors raised by the containerd backend and its runtime profiles."""

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


class ProfileNotApplicable(BackendAIError, web.HTTPBadRequest):
    """Raised when no runtime profile accepts a kernel that requires one."""

    error_type = "https://api.backend.ai/probs/agent/runtime-profile-not-applicable"
    error_title = "No runtime profile accepts the kernel."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.MISMATCH,
        )


class ProfileSpecRejected(BackendAIError, web.HTTPBadRequest):
    """Raised when a runtime profile rejects the kernel spec it is asked to plan."""

    error_type = "https://api.backend.ai/probs/agent/runtime-profile-spec-rejected"
    error_title = "The runtime profile rejected the kernel spec."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class RuntimeProfileLoadError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a configured runtime profile cannot be loaded."""

    error_type = "https://api.backend.ai/probs/agent/runtime-profile-load-failed"
    error_title = "A runtime profile cannot be loaded."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
