"""Query orders for app config definition rows."""

from __future__ import annotations

from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("AppConfigDefinitionOrders",)


class AppConfigDefinitionOrders:
    @staticmethod
    def config_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigDefinitionRow.config_name.asc()
        return AppConfigDefinitionRow.config_name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigDefinitionRow.created_at.asc()
        return AppConfigDefinitionRow.created_at.desc()
