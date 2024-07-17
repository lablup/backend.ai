class RBACException(Exception):
    pass


class InvalidScope(RBACException):
    pass


class NotEnoughPermission(RBACException):
    pass
