from typing import Any

from ai.backend.client.exceptions import BackendAPIError, BackendClientError


class InvalidRequestError(BackendAPIError):
    """HTTP 400 Bad Request."""


class AuthenticationError(BackendAPIError):
    """HTTP 401 Unauthorized."""


class PermissionDeniedError(BackendAPIError):
    """HTTP 403 Forbidden."""


class NotFoundError(BackendAPIError):
    """HTTP 404 Not Found."""


class ConflictError(BackendAPIError):
    """HTTP 409 Conflict."""


class TooManyRequestsError(BackendAPIError):
    """HTTP 429 Too Many Requests."""


class ServerError(BackendAPIError):
    """HTTP 500+ Server Error."""


STATUS_CODE_EXCEPTION_MAP: dict[int, type[BackendAPIError]] = {
    400: InvalidRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    429: TooManyRequestsError,
}


class WebSocketError(BackendClientError):
    """Error during WebSocket connection or communication."""


class SSEError(BackendClientError):
    """Error during SSE connection or stream processing."""


def map_status_to_exception(
    status: int,
    reason: str,
    data: Any,
) -> BackendAPIError:
    exc_cls = STATUS_CODE_EXCEPTION_MAP.get(status)
    if exc_cls is not None:
        return exc_cls(status, reason, data)
    if status >= 500:
        return ServerError(status, reason, data)
    return BackendAPIError(status, reason, data)
