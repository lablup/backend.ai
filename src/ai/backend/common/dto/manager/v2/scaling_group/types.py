"""
Common types for scaling group DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "PreemptionMode",
    "PreemptionOrder",
    "ScalingGroupOrderField",
    "SchedulerType",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ScalingGroupOrderField(StrEnum):
    """Fields available for ordering scaling groups."""

    NAME = "name"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"


class SchedulerType(StrEnum):
    """Scheduler type for session scheduling.

    Re-defined in DTO namespace to avoid importing from manager/data layer.
    """

    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIR_SHARE = "fair-share"


class PreemptionMode(StrEnum):
    """Preemption mode for session preemption.

    Re-defined in DTO namespace to avoid importing from manager/data layer.
    """

    TERMINATE = "terminate"
    RESCHEDULE = "reschedule"


class PreemptionOrder(StrEnum):
    """Preemption order for selecting sessions to preempt.

    Re-defined in DTO namespace to avoid importing from manager/data layer.
    """

    OLDEST = "oldest"
    NEWEST = "newest"
