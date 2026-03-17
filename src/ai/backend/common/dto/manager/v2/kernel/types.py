"""Common types for kernel DTO v2."""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "KernelOrderField",
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
