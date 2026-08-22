"""Query orders for scaling group rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.resource_group import ResourceGroupRow

__all__ = ("ResourceGroupOrders",)


class ResourceGroupOrders:
    """Query orders for scaling groups."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceGroupRow.name.asc()
        return ResourceGroupRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceGroupRow.created_at.asc()
        return ResourceGroupRow.created_at.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceGroupRow.is_active.asc()
        return ResourceGroupRow.is_active.desc()

    @staticmethod
    def is_public(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ResourceGroupRow.is_public.asc()
        return ResourceGroupRow.is_public.desc()
