"""Query orders for app config allow-list rows."""

from __future__ import annotations

from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("AppConfigAllowListOrders",)


class AppConfigAllowListOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigAllowListRow.id.asc()
        return AppConfigAllowListRow.id.desc()

    @staticmethod
    def config_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigAllowListRow.config_name.asc()
        return AppConfigAllowListRow.config_name.desc()

    @staticmethod
    def scope_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigAllowListRow.scope_type.asc()
        return AppConfigAllowListRow.scope_type.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigAllowListRow.created_at.asc()
        return AppConfigAllowListRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigAllowListRow.updated_at.asc()
        return AppConfigAllowListRow.updated_at.desc()
