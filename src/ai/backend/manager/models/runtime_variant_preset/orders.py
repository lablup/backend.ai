"""Query orders for runtime variant preset rows."""

from __future__ import annotations

from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("RuntimeVariantPresetOrders",)


class RuntimeVariantPresetOrders:
    @staticmethod
    def rank(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.rank.asc()
        return RuntimeVariantPresetRow.rank.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.name.asc()
        return RuntimeVariantPresetRow.name.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.id.asc()
        return RuntimeVariantPresetRow.id.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.created_at.asc()
        return RuntimeVariantPresetRow.created_at.desc()
