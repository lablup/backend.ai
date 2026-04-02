"""Query orders for resource preset rows."""

from __future__ import annotations

from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("ResourcePresetOrders",)


class ResourcePresetOrders:
    """Query orders for resource presets."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourcePresetRow.name.asc()
        return ResourcePresetRow.name.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourcePresetRow.id.asc()
        return ResourcePresetRow.id.desc()
