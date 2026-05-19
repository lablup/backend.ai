"""
Containerd-backend-related agent exceptions.

These are raised at agent startup pre-flight, before any kernel work happens,
to surface CNI / containerd misconfigurations with a clear root cause.
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


class CniBinaryMissingError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a required CNI plugin binary is absent from cni_bin_dir."""

    error_type = "https://api.backend.ai/probs/agent/containerd-cni-binary-missing"
    error_title = "Required CNI plugin binary is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class CniConflistMissingError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the named CNI conflist cannot be found in cni_conf_dir."""

    error_type = "https://api.backend.ai/probs/agent/containerd-cni-conflist-missing"
    error_title = "CNI conflist not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class CniConflistInvalidError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a CNI conflist exists but cannot be parsed as valid JSON."""

    error_type = "https://api.backend.ai/probs/agent/containerd-cni-conflist-invalid"
    error_title = "CNI conflist is invalid."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class CniPortmapMissingError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a CNI conflist's plugin chain does not include 'portmap'.

    The portmap plugin is what provides container-port → host-port forwarding.
    Without it, Backend.AI service ports (Jupyter, SSH, TensorBoard, …) cannot
    be reached from outside the pod, breaking the App Proxy integration.
    """

    error_type = "https://api.backend.ai/probs/agent/containerd-cni-portmap-missing"
    error_title = "CNI conflist does not chain the portmap plugin."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class CniConfDirNotWritableError(BackendAIError, web.HTTPInternalServerError):
    """Raised when 'managed' mode is selected but cni_conf_dir is not writable."""

    error_type = "https://api.backend.ai/probs/agent/containerd-cni-conf-dir-not-writable"
    error_title = "CNI conf dir is not writable."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class CriConnectionError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the CRI gRPC channel cannot be established or is lost."""

    error_type = "https://api.backend.ai/probs/agent/containerd-cri-connection-error"
    error_title = "CRI gRPC connection error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class CriRpcError(BackendAIError, web.HTTPInternalServerError):
    """Wraps a non-recoverable gRPC error returned by the runtime.

    Specific operations may map gRPC status codes to more precise
    BackendAIError subclasses; this is the catch-all for operations
    that do not yet have specialized error classes.
    """

    error_type = "https://api.backend.ai/probs/agent/containerd-cri-rpc-error"
    error_title = "CRI RPC error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ContainerdConnectionError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the containerd native-API gRPC channel cannot be established or is lost."""

    error_type = "https://api.backend.ai/probs/agent/containerd-connection-error"
    error_title = "containerd gRPC connection error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class ContainerdRpcError(BackendAIError, web.HTTPInternalServerError):
    """Wraps a non-recoverable gRPC error returned by containerd's native API.

    Specific operations may map gRPC status codes to more precise
    BackendAIError subclasses; this is the catch-all for operations
    that do not yet have specialized error classes.
    """

    error_type = "https://api.backend.ai/probs/agent/containerd-rpc-error"
    error_title = "containerd RPC error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NetnsSetupError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a workload's network namespace cannot be created or removed."""

    error_type = "https://api.backend.ai/probs/agent/containerd-netns-setup-error"
    error_title = "Network namespace setup failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class CniInvocationError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a CNI plugin invocation fails or returns an invalid result."""

    error_type = "https://api.backend.ai/probs/agent/containerd-cni-invocation-error"
    error_title = "CNI plugin invocation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
