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
    """Fields available for ordering object storages.

    ``CREATED_AT`` is deprecated since 26.9.0: the table has no such column, so the
    value is not used for ordering. It is removed in the next release.
    """

    NAME = "name"
    HOST = "host"
    REGION = "region"
    CREATED_AT = "created_at"
