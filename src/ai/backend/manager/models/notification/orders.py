"""Query orders for notification entities."""

from __future__ import annotations

from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base import QueryOrder


class NotificationChannelOrders:
    """Query orders for notification channels."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.name.asc()
        return NotificationChannelRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.created_at.asc()
        return NotificationChannelRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.updated_at.asc()
        return NotificationChannelRow.updated_at.desc()


class NotificationRuleOrders:
    """Query orders for notification rules."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.name.asc()
        return NotificationRuleRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.created_at.asc()
        return NotificationRuleRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.updated_at.asc()
        return NotificationRuleRow.updated_at.desc()
