"""Common types for compute_cluster DTO v2."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.query import EnumFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "ComputeClusterOrderField",
    "ComputeClusterStatus",
    "ComputeClusterStatusFilter",
    "OrderDirection",
)


class ComputeClusterStatus(StrEnum):
    """Whether the manager reaches a compute cluster's API server."""

    UNKNOWN = "UNKNOWN"
    ALIVE = "ALIVE"
    LOST = "LOST"


class ComputeClusterStatusFilter(EnumFilter[ComputeClusterStatus]):
    """Filter for compute cluster status values."""


class ComputeClusterOrderField(StrEnum):
    """Fields available for ordering compute clusters."""

    NAME = "name"
    CREATED_AT = "created_at"
