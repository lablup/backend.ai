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


class ContainerdUnavailableError(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when the containerd socket cannot be used."""

    error_type = "https://api.backend.ai/probs/agent/containerd-unavailable"
    error_title = "The containerd daemon is unavailable."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ContainerdOperationFailed(BackendAIError, web.HTTPInternalServerError):
    """Raised when a containerd gRPC call fails."""

    error_type = "https://api.backend.ai/probs/agent/containerd-operation-failed"
    error_title = "A containerd operation failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ContainerdImageNotFound(BackendAIError, web.HTTPNotFound):
    """Raised when the image is not in the containerd image store of the namespace."""

    error_type = "https://api.backend.ai/probs/agent/containerd-image-not-found"
    error_title = "The image is not imported into containerd."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ContainerdImageInvalid(BackendAIError, web.HTTPInternalServerError):
    """Raised when an image in the containerd store has no usable manifest or config."""

    error_type = "https://api.backend.ai/probs/agent/containerd-image-invalid"
    error_title = "The image in containerd cannot be used."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class KrunnerEnvironmentError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the kernel runner environment cannot be extracted."""

    error_type = "https://api.backend.ai/probs/agent/krunner-environment-failed"
    error_title = "The kernel runner environment cannot be prepared."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelNetworkSetupFailed(BackendAIError, web.HTTPInternalServerError):
    """Raised when a host network command for a kernel (ip, iptables, sysctl) fails."""

    error_type = "https://api.backend.ai/probs/agent/kernel-network-setup-failed"
    error_title = "The kernel network cannot be set up."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelAddressExhausted(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when the bridge subnet has no free address left for a kernel."""

    error_type = "https://api.backend.ai/probs/agent/kernel-address-exhausted"
    error_title = "No kernel address is available on the bridge."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ReadinessTimeout(BackendAIError, web.HTTPGatewayTimeout):
    """Raised when a kernel is not ready within the readiness timeout of its launch plan."""

    error_type = "https://api.backend.ai/probs/agent/kernel-readiness-timeout"
    error_title = "The kernel did not become ready within the profile's readiness timeout."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.TIMEOUT,
        )


class SealedSpecMissing(BackendAIError, web.HTTPBadRequest):
    """Raised when a sealed kernel is created without the signature of its launch spec."""

    error_type = "https://api.backend.ai/probs/agent/sealed-spec-missing"
    error_title = "A sealed kernel has no spec signature."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
