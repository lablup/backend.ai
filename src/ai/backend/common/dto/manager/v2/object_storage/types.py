"""
Common types for object_storage DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "ObjectStorageOrderField",
    "OrderDirection",
)


class ObjectStorageOrderField(StrEnum):
    """Fields available for ordering object storages."""

    NAME = "name"
    HOST = "host"
    REGION = "region"
    CREATED_AT = "created_at"
