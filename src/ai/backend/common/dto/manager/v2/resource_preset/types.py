"""Types for resource preset v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "ResourcePresetOrderDirection",
    "ResourcePresetOrderField",
)


class ResourcePresetOrderField(StrEnum):
    """Fields available for ordering resource presets."""

    NAME = "name"


class ResourcePresetOrderDirection(StrEnum):
    """Order direction for resource preset search results."""

    ASC = "asc"
    DESC = "desc"
