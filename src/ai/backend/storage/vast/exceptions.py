from typing import Optional


class VastError(Exception):
    pass


class VastAPIError(VastError):
    message: str

    def __init__(self, message: Optional[str] = None, *args):
        super().__init__(message, *args)

        self.message = message or ""

    def __str__(self) -> str:
        return type(self).__name__


class VastUnauthorizedError(VastAPIError):
    pass


class VastInvalidParameterError(VastAPIError):
    pass


class VastNotFoundError(VastAPIError):
    pass


class VastClusterNotFoundError(VastAPIError):
    pass


class VastUnknownError(VastAPIError):
    pass
