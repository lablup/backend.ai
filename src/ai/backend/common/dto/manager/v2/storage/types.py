"""
Common types for storage DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "StorageOrderField",
)


class StorageOrderField(StrEnum):
    """Fields available for ordering storages."""

    NAME = "name"
    HOST = "host"
