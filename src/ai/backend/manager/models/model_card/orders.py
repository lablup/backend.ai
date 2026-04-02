"""Query orders for model card rows."""

from __future__ import annotations

from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("ModelCardOrders",)


class ModelCardOrders:
    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ModelCardRow.name.asc()
        return ModelCardRow.name.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ModelCardRow.id.asc()
        return ModelCardRow.id.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ModelCardRow.created_at.asc()
        return ModelCardRow.created_at.desc()
