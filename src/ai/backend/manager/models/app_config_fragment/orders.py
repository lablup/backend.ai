"""Query orders for the app_config_fragment domain."""

from __future__ import annotations

from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import QueryOrder


class AppConfigFragmentOrders:
    """QueryOrder factories for app-config fragment sorting."""

    @staticmethod
    def scope_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.scope_type.asc()
        return AppConfigFragmentRow.scope_type.desc()

    @staticmethod
    def scope_id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.scope_id.asc()
        return AppConfigFragmentRow.scope_id.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.name.asc()
        return AppConfigFragmentRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.created_at.asc()
        return AppConfigFragmentRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.updated_at.asc()
        return AppConfigFragmentRow.updated_at.desc()
