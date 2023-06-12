from typing import Optional


class DellError(Exception):
    pass


class DellInitError(DellError):
    pass


class DellAPIError(DellError):
    message: str

    def __init__(self, message: Optional[str] = None, *args):
        super().__init__(message, *args)

        self.message = message or ""

    def __str__(self) -> str:
        return type(self).__name__


class DellInvalidBodyError(DellAPIError):
    pass


class DellUnauthorizedError(DellAPIError):
    pass


class DellNotFoundError(DellAPIError):
    pass


class DellInternalError(DellAPIError):
    pass


class DellNoMetricError(DellError):
    pass
