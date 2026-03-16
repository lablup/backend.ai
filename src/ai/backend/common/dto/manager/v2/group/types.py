"""
Common types for Group (Project) DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "GroupOrderField",
    "OrderDirection",
    "ProjectType",
)


class ProjectType(StrEnum):
    """Project type determining its purpose and behavior."""

    GENERAL = "general"
    MODEL_STORE = "model-store"


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class GroupOrderField(StrEnum):
    """Fields available for ordering groups."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
