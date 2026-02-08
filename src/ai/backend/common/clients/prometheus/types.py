from enum import StrEnum


class ValueType(StrEnum):
    """Specifies the type of a metric value."""

    CURRENT = "current"
    CAPACITY = "capacity"
