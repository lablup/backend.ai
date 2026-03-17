"""
Common types for resource group DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "ResourceGroupOrderDirection",
    "ResourceGroupOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ResourceGroupOrderDirection(StrEnum):
    """Order direction for resource group sorting."""

    ASC = "asc"
    DESC = "desc"


class ResourceGroupOrderField(StrEnum):
    """Fields available for ordering resource groups."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
