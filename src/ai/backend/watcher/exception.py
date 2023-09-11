class WatcherError(Exception):
    pass


class InvalidWatcher(WatcherError):
    pass


class AuthorizationFailed(WatcherError):
    pass
