"""
Common types for quota_scope DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "QuotaScopeOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class QuotaScopeOrderField(StrEnum):
    """Fields available for ordering quota scopes."""

    QUOTA_SCOPE_ID = "quota_scope_id"
    STORAGE_HOST_NAME = "storage_host_name"
