"""DataQuerier implementations for the notification repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import (
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.manager.data.notification.types import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.models.notification.row import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class NotificationChannelQuerier(DataQuerier[NotificationChannelRow, NotificationChannelData]):
    channel_id: NotificationChannelID

    @override
    def row_class(self) -> type[NotificationChannelRow]:
        return NotificationChannelRow

    @override
    def pk_value(self) -> NotificationChannelID:
        return self.channel_id

    @override
    def to_data(self, row: NotificationChannelRow) -> NotificationChannelData:
        return row.to_data()


@dataclass
class NotificationRuleQuerier(DataQuerier[NotificationRuleRow, NotificationRuleData]):
    rule_id: NotificationRuleID

    @override
    def row_class(self) -> type[NotificationRuleRow]:
        return NotificationRuleRow

    @override
    def pk_value(self) -> NotificationRuleID:
        return self.rule_id

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return row.to_data()
