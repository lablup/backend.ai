class RBACException(Exception):
    pass


class NotEnoughPermission(RBACException):
    pass
