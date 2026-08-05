"""Query orders for retention policy rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.retention.row import RetentionPolicyRow

__all__ = ("RetentionPolicyOrders",)


class RetentionPolicyOrders:
    @staticmethod
    def category(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RetentionPolicyRow.category.asc()
        return RetentionPolicyRow.category.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RetentionPolicyRow.created_at.asc()
        return RetentionPolicyRow.created_at.desc()

    @staticmethod
    def last_swept_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RetentionPolicyRow.last_swept_at.asc()
        return RetentionPolicyRow.last_swept_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RetentionPolicyRow.id.asc()
        return RetentionPolicyRow.id.desc()
