from typing import Optional


class GPFSError(Exception):
    message: str

    def __init__(self, message: Optional[str] = None, *args):
        super().__init__(message, *args)

        self.message = message or ""

    def __str__(self) -> str:
        return type(self).__name__


class GPFSInitError(GPFSError):
    pass


class GPFSAPIError(GPFSError):
    pass


class GPFSInvalidBodyError(GPFSAPIError):
    pass


class GPFSUnauthorizedError(GPFSAPIError):
    pass


class GPFSNotFoundError(GPFSAPIError):
    pass


class GPFSInternalError(GPFSAPIError):
    pass


class GPFSNoMetricError(GPFSError):
    pass


class GPFSJobFailedError(GPFSError):
    pass


class GPFSJobCancelledError(GPFSError):
    pass
