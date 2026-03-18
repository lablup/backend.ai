"""
Common types for config DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.config.types import (
    MAXIMUM_DOTFILE_SIZE,
    DotfilePermission,
)

__all__ = (
    "MAXIMUM_DOTFILE_SIZE",
    "DotfileOrderField",
    "DotfilePermission",
    "DotfileScope",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class DotfileScope(StrEnum):
    """Scope of a dotfile."""

    USER = "user"
    GROUP = "group"
    DOMAIN = "domain"


class DotfileOrderField(StrEnum):
    """Fields available for ordering dotfiles."""

    NAME = "name"
    CREATED_AT = "created_at"
