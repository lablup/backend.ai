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


class KernelRecoveryDataParseError(BackendAIError):
    error_type = "https://api.backend.ai/probs/kernel-recovery-data-parse-error"
    error_title = "Failed to parse kernel recovery data"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class UnsupportedKernelType(BackendAIError):
    """A kernel this registry cannot write down, or a record it cannot rebuild.

    Raised rather than skipped. A backend whose kernels are silently left out of the registry
    still starts, still runs sessions, and loses every one of them at the next restart -- and says
    nothing at any point, because "wrote no entries" and "had no entries" look the same.
    """

    error_type = "https://api.backend.ai/probs/unsupported-kernel-type"
    error_title = "Unsupported kernel type for recovery"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )
