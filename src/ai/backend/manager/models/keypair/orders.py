"""Query orders for keypair rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.keypair.row import KeyPairRow

__all__ = ("KeypairOrders",)


class KeypairOrders:
    """Query orders for sorting keypairs."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.created_at.asc()
        return KeyPairRow.created_at.desc()

    @staticmethod
    def last_used(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.last_used.asc()
        return KeyPairRow.last_used.desc()

    @staticmethod
    def access_key(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.access_key.asc()
        return KeyPairRow.access_key.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.is_active.asc()
        return KeyPairRow.is_active.desc()

    @staticmethod
    def is_default(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.is_default.asc()
        return KeyPairRow.is_default.desc()

    @staticmethod
    def resource_policy(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.resource_policy.asc()
        return KeyPairRow.resource_policy.desc()
