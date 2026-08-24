"""Common types for Label DTO v2."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "EntityLabelOrderField",
    "OrderDirection",
)


class EntityLabelOrderField(StrEnum):
    """Fields available for ordering labels."""

    KEY = "key"
    VALUE = "value"
    CREATED_AT = "created_at"
