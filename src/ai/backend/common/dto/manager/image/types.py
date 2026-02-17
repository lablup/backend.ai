"""
Common types for image management REST API.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "ImageOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ImageOrderField(StrEnum):
    """Fields available for ordering images."""

    NAME = "name"
    CREATED_AT = "created_at"
