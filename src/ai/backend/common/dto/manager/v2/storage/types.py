"""
Common types for storage DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "StorageOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class StorageOrderField(StrEnum):
    """Fields available for ordering storages."""

    NAME = "name"
    HOST = "host"
