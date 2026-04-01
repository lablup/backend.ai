"""
Common types for VFolder DTO system.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "VFolderOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class VFolderOrderField(StrEnum):
    """Fields available for ordering vfolders."""

    NAME = "name"
    CREATED_AT = "created_at"
    STATUS = "status"
    USAGE_MODE = "usage_mode"
    HOST = "host"
