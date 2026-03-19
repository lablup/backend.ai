"""Common types for kernel DTO v2."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "KernelOrderField",
    "KernelStatusEnum",
    "KernelStatusFilter",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class KernelOrderField(StrEnum):
    """Fields available for ordering kernel search."""

    CLUSTER_IDX = "cluster_idx"
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"
    STATUS = "status"
    CLUSTER_MODE = "cluster_mode"
    CLUSTER_HOSTNAME = "cluster_hostname"


class KernelStatusEnum(StrEnum):
    """Kernel lifecycle status values for DTO filtering."""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"


class KernelStatusFilter(BaseRequestModel):
    """Filter for kernel status values."""

    in_: list[KernelStatusEnum] | None = None
    not_in: list[KernelStatusEnum] | None = None
