from typing import Optional


class WekaError(Exception):
    pass


class WekaInitError(WekaError):
    pass


class WekaAPIError(WekaError):
    message: str

    def __init__(self, message: Optional[str] = None, *args):
        super().__init__(message, *args)

        self.message = message or ""

    def __str__(self) -> str:
        return type(self).__name__


class WekaInvalidBodyError(WekaAPIError):
    pass


class WekaUnauthorizedError(WekaAPIError):
    pass


class WekaNotFoundError(WekaAPIError):
    pass


class WekaInternalError(WekaAPIError):
    pass


class WekaNoMetricError(WekaError):
    pass
