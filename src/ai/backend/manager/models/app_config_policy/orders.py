"""Query orders for the app_config_policy domain."""

from __future__ import annotations

from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.base import QueryOrder


class AppConfigPolicyOrders:
    """QueryOrder factories for app-config policy sorting."""

    @staticmethod
    def config_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigPolicyRow.config_name.asc()
        return AppConfigPolicyRow.config_name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigPolicyRow.created_at.asc()
        return AppConfigPolicyRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AppConfigPolicyRow.updated_at.asc()
        return AppConfigPolicyRow.updated_at.desc()
