"""Service-related errors for App Proxy."""

from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class WorkerNotAvailable(BackendAIError):
    """Raised when worker is not available."""

    error_type = "https://api.backend.ai/probs/appproxy/worker-not-available"
    error_title = "Worker not available."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class PortNotAvailable(BackendAIError):
    """Raised when designated port is already occupied."""

    error_type = "https://api.backend.ai/probs/appproxy/port-not-available"
    error_title = "Designated port already occupied."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class UnsupportedProtocol(BackendAIError):
    """Raised when protocol is not supported."""

    error_type = "https://api.backend.ai/probs/appproxy/unsupported-protocol"
    error_title = "Unsupported protocol."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class DatabaseError(BackendAIError):
    """Raised when error occurs while communicating with database."""

    error_type = "https://api.backend.ai/probs/appproxy/database-error"
    error_title = "Error while communicating with database."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DATABASE,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ContainerConnectionRefused(BackendAIError):
    """Raised when connection to Backend.AI kernel is refused."""

    error_type = "https://api.backend.ai/probs/appproxy/container-connection-refused"
    error_title = "Cannot connect to Backend.AI kernel."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class WorkerRegistrationError(BackendAIError):
    """Raised when worker registration fails."""

    error_type = "https://api.backend.ai/probs/appproxy/worker-registration-error"
    error_title = "E20013: Failed to register worker."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class CoordinatorConnectionError(BackendAIError):
    """Raised when communication with coordinator fails."""

    error_type = "https://api.backend.ai/probs/appproxy/coordinator-connection-error"
    error_title = "E20014: Failed to communicate with coordinator."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNREACHABLE,
        )
