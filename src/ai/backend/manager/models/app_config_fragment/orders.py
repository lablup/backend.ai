"""Query orders for app config fragment rows."""

from __future__ import annotations

from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.clauses import QueryOrder

__all__ = ("AppConfigFragmentOrders",)


class AppConfigFragmentOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.id.asc()
        return AppConfigFragmentRow.id.desc()

    @staticmethod
    def config_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.config_name.asc()
        return AppConfigFragmentRow.config_name.desc()

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
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.created_at.asc()
        return AppConfigFragmentRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigFragmentRow.updated_at.asc()
        return AppConfigFragmentRow.updated_at.desc()
