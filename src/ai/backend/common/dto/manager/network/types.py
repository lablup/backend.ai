"""
Common types for network system.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "NetworkOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class NetworkOrderField(StrEnum):
    """Fields available for ordering networks."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
