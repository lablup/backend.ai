"""Query orders for runtime variant rows."""

from __future__ import annotations

from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("RuntimeVariantOrders",)


class RuntimeVariantOrders:
    """Query orders for runtime variants."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantRow.name.asc()
        return RuntimeVariantRow.name.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantRow.id.asc()
        return RuntimeVariantRow.id.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantRow.created_at.asc()
        return RuntimeVariantRow.created_at.desc()
