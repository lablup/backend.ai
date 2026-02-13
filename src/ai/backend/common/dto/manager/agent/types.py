"""
Common types for Agent REST API.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "AgentOrderField",
    "AgentStatusFilter",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class AgentStatusFilter(StrEnum):
    """Agent statuses available for filtering."""

    ALIVE = "ALIVE"
    LOST = "LOST"
    RESTARTING = "RESTARTING"
    TERMINATED = "TERMINATED"


class AgentOrderField(StrEnum):
    """Fields available for ordering agents."""

    ID = "id"
    STATUS = "status"
    SCALING_GROUP = "scaling_group"
