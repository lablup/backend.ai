import json
from typing import Any

__all__ = (
    "BackendError",
    "BackendAPIError",
    "BackendClientError",
    "APIVersionWarning",
)


class BackendError(Exception):
    """Exception type to catch all ai.backend-related errors."""

    def __str__(self):
        return repr(self)


class BackendAPIError(BackendError):
    """Exceptions returned by the API gateway."""

    def __init__(self, status: int, reason: str, data: Any):
        if isinstance(data, (str, bytes)):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                data = {
                    "type": "https://api.backend.ai/probs/generic-error",
                    "title": "Generic Error (could not parse error string)",
                    "content": data,
                }
        super().__init__(status, reason, data)

    @property
    def status(self) -> int:
        return self.args[0]

    @property
    def reason(self) -> str:
        return self.args[1]

    @property
    def data(self) -> Any:
        return self.args[2]


class BackendAPIVersionError(BackendError):
    """
    Exception indicating that the given operation/argument is not supported
    in the currently negotiated server API version.
    """


class BackendClientError(BackendError):
    """
    Exceptions from the client library, such as argument validation
    errors and connection failures.
    """

    pass


class APIVersionWarning(UserWarning):
    """
    The warning generated if the server's API version is higher.
    """

    pass
