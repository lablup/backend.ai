from typing import override

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class KernelRegistryLoadError(BackendAIError):
    error_type = "https://api.backend.ai/probs/kernel-registry-load-error"
    error_title = "Failed to load kernel registry"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class KernelRegistryNotFound(BackendAIError):
    error_type = "https://api.backend.ai/probs/kernel-registry-not-found"
    error_title = "Kernel registry not found"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
