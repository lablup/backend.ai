class EmptySQLCondition(Exception):
    """
    Exception raised when an SQL condition is empty, which leads to DB full table scan.
    """


class ObjectNotFound(Exception):
    """
    Exception raised when an object is not found.
    """
