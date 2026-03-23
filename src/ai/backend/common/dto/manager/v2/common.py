"""Shared types used across all v2 DTO domains."""

from __future__ import annotations

from enum import StrEnum

__all__ = ("OrderDirection",)


class OrderDirection(StrEnum):
    """Order direction for sorting. Shared across all v2 DTO domains."""

    ASC = "ASC"
    DESC = "DESC"
