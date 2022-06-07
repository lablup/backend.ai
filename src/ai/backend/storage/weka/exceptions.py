class WekaError(Exception):
    pass


class WekaInitError(WekaError):
    pass


class WekaAPIError(WekaError):
    pass


class WekaNotFoundError(WekaAPIError):
    pass


class WekaUnauthorizedError(WekaAPIError):
    pass


class WekaNoMetricError(WekaError):
    pass
