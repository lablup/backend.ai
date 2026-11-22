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


class KernelPathNotAllowedError(BackendAIError, web.HTTPForbidden):
    """A file operation names a path outside the kernel's home directory."""

    error_type = "https://api.backend.ai/probs/kube/kernel-path-not-allowed"
    error_title = "The path is outside the kernel's home directory."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class KernelFileNotFoundError(BackendAIError, web.HTTPNotFound):
    """The file or directory a file operation names does not exist in the kernel."""

    error_type = "https://api.backend.ai/probs/kube/kernel-file-not-found"
    error_title = "The file is not found in the kernel."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KernelFileTooLargeError(BackendAIError, web.HTTPBadRequest):
    """A download or an exec output exceeds its size limit."""

    error_type = "https://api.backend.ai/probs/kube/kernel-file-too-large"
    error_title = "The data exceeds the size limit."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class KernelExecTimeoutError(BackendAIError, web.HTTPGatewayTimeout):
    """A command the gateway runs in a kernel container did not finish in time."""

    error_type = "https://api.backend.ai/probs/kube/kernel-exec-timeout"
    error_title = "The command in the kernel container timed out."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.TIMEOUT,
        )


class KernelExecFailedError(BackendAIError, web.HTTPInternalServerError):
    """A command the gateway runs in a kernel container failed."""

    error_type = "https://api.backend.ai/probs/kube/kernel-exec-failed"
    error_title = "The command in the kernel container failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
