"""
Common types for resource group DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "PreemptionModeDTO",
    "PreemptionOrderDTO",
    "ResourceGroupOrderDirection",
    "ResourceGroupOrderField",
    "SchedulerTypeDTO",
)


class ResourceGroupOrderDirection(StrEnum):
    """Order direction for resource group sorting."""

    ASC = "ASC"
    DESC = "DESC"


class ResourceGroupOrderField(StrEnum):
    """Fields available for ordering resource groups."""

    NAME = "name"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"


class SchedulerTypeDTO(StrEnum):
    """Scheduler type for resource group."""

    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIR_SHARE = "fair-share"


class PreemptionOrderDTO(StrEnum):
    """Tie-breaking order for same-priority sessions during preemption."""

    OLDEST = "oldest"
    NEWEST = "newest"


class PreemptionModeDTO(StrEnum):
    """How to preempt a session when preemption is triggered."""

    TERMINATE = "terminate"
    RESCHEDULE = "reschedule"
