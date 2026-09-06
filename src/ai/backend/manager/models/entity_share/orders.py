"""Query orders for entity invitation rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.entity_share.row import EntityShareRow

__all__ = ("EntityShareOrders",)


class EntityShareOrders:
    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityShareRow.created_at.asc()
        return EntityShareRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityShareRow.updated_at.asc()
        return EntityShareRow.updated_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityShareRow.status.asc()
        return EntityShareRow.status.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityShareRow.id.asc()
        return EntityShareRow.id.desc()
