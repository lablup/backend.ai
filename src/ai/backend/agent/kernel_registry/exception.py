from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class KernelRegistryLoadError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-registry-load-error"
    error_title = "Failed to load kernel registry"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class KernelRegistryNotFound(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-registry-not-found"
    error_title = "Kernel registry not found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KernelRecoveryDataParseError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-recovery-data-parse-error"
    error_title = "Failed to parse kernel recovery data"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
