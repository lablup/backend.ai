from dataclasses import dataclass
from enum import StrEnum


class ValueType(StrEnum):
    """Specifies the type of a metric value."""

    CURRENT = "current"
    CAPACITY = "capacity"
    PCT = "pct"


@dataclass(frozen=True)
class MetricValue:
    """A single metric sample with its name, value type, and raw value."""

    metric_name: str
    value_type: ValueType
    value: str
