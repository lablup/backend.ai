class WekaError(Exception):
    pass


class WekaInitError(WekaError):
    pass


class WekaAPIError(WekaError):
    name = 'WekaAPIError'
    message = ''

    def __init__(self, message: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.message = message or 'Unknown Error'

    def __str__(self) -> str:
        return f'{self.name}: {self.message}'


class WekaInvalidBodyError(WekaAPIError):
    name = 'WekaInvalidBodyError'


class WekaUnauthorizedError(WekaAPIError):
    name = 'WekaUnauthorizedError'


class WekaNotFoundError(WekaAPIError):
    name = 'WekaNotFoundError'


class WekaInternalError(WekaAPIError):
    name = 'WekaInternalError'


class WekaNoMetricError(WekaError):
    pass
