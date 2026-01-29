class VASTError(Exception):
    pass


class VASTAPIError(VASTError):
    message: str

    def __init__(self, message: str | None = None, *args) -> None:
        super().__init__(message, *args)

        self.message = message or ""

    def __str__(self) -> str:
        return type(self).__name__


class VASTUnauthorizedError(VASTAPIError):
    pass


class VASTInvalidParameterError(VASTAPIError):
    pass


class VASTNotFoundError(VASTAPIError):
    pass


class VASTClusterNotFoundError(VASTAPIError):
    pass


class VASTUnknownError(VASTAPIError):
    pass
