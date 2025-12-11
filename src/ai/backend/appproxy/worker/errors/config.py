"""
Configuration-related exceptions for the worker.
"""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class MissingTraefikConfigError(BackendAIError):
    """Raised when Traefik configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/missing-traefik-config"
    error_title = "Traefik configuration is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingAnnounceAddressError(BackendAIError):
    """Raised when announce address is missing."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/missing-announce-address"
    error_title = "Announce address is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingProfilingConfigError(BackendAIError):
    """Raised when profiling configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/missing-profiling-config"
    error_title = "Profiling configuration is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingPortConfigError(BackendAIError):
    """Raised when port configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/missing-port-config"
    error_title = "Port configuration is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MissingPortProxyConfigError(BackendAIError):
    """Raised when port proxy configuration is missing."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/missing-port-proxy-config"
    error_title = "Port proxy configuration is missing."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class CleanupContextNotInitializedError(BackendAIError):
    """Raised when cleanup context is not initialized."""

    error_type = "https://api.backend.ai/probs/appproxy-worker/cleanup-context-not-initialized"
    error_title = "Cleanup context is not initialized."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )
