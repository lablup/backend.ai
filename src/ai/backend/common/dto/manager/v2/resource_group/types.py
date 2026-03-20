"""
Common types for resource group DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "ResourceGroupOrderDirection",
    "ResourceGroupOrderField",
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
