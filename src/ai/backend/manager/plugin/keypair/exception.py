class ExternalError(Exception):
    pass


class InvalidSToken(ExternalError):
    pass


class ExpiredSToken(ExternalError):
    pass
