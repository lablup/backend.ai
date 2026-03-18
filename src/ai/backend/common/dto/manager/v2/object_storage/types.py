"""
Common types for object_storage DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "ObjectStorageOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ObjectStorageOrderField(StrEnum):
    """Fields available for ordering object storages."""

    NAME = "name"
    HOST = "host"
    REGION = "region"
    CREATED_AT = "created_at"
