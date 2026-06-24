"""Query orders for app config definition rows."""

from __future__ import annotations

from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.query_types import QueryOrder

__all__ = ("AppConfigDefinitionOrders",)


class AppConfigDefinitionOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigDefinitionRow.id.asc()
        return AppConfigDefinitionRow.id.desc()

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

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigDefinitionRow.updated_at.asc()
        return AppConfigDefinitionRow.updated_at.desc()
