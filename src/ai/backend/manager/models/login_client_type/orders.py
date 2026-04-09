"""Query orders for the login_client_type domain."""

from __future__ import annotations

from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.base import QueryOrder


class LoginClientTypeOrders:
    """QueryOrder factories for login client type sorting."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        col = LoginClientTypeRow.name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        col = LoginClientTypeRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        col = LoginClientTypeRow.modified_at
        return col.asc() if ascending else col.desc()
