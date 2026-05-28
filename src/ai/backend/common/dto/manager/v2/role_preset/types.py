"""Types for role preset v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

__all__ = ("RolePresetOrderField",)


class RolePresetOrderField(StrEnum):
    """Fields available for ordering role presets."""

    NAME = "name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
