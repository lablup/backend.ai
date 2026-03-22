"""
Common types for config DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.config.types import (
    MAXIMUM_DOTFILE_SIZE,
    DotfilePermission,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "MAXIMUM_DOTFILE_SIZE",
    "DotfileOrderField",
    "DotfilePermission",
    "DotfileScope",
    "OrderDirection",
)


class DotfileScope(StrEnum):
    """Scope of a dotfile."""

    USER = "user"
    GROUP = "group"
    DOMAIN = "domain"


class DotfileOrderField(StrEnum):
    """Fields available for ordering dotfiles."""

    NAME = "name"
    CREATED_AT = "created_at"
