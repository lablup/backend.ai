"""Query orders for entity invitation rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow

__all__ = ("EntityInvitationOrders",)


class EntityInvitationOrders:
    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityInvitationRow.created_at.asc()
        return EntityInvitationRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityInvitationRow.updated_at.asc()
        return EntityInvitationRow.updated_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityInvitationRow.status.asc()
        return EntityInvitationRow.status.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EntityInvitationRow.id.asc()
        return EntityInvitationRow.id.desc()
