"""Query orders for client IP masking policy rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow

__all__ = ("ClientIPMaskingPolicyOrders",)


class ClientIPMaskingPolicyOrders:
    @staticmethod
    def target_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ClientIPMaskingPolicyRow.target_type.asc()
        return ClientIPMaskingPolicyRow.target_type.desc()

    @staticmethod
    def mode(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ClientIPMaskingPolicyRow.mode.asc()
        return ClientIPMaskingPolicyRow.mode.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ClientIPMaskingPolicyRow.created_at.asc()
        return ClientIPMaskingPolicyRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ClientIPMaskingPolicyRow.updated_at.asc()
        return ClientIPMaskingPolicyRow.updated_at.desc()
