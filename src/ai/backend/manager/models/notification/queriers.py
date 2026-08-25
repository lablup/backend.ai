"""DataQuerier implementations for the notification repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

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
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return NotificationChannelRow.id

    @override
    def entity_id_value(self) -> NotificationChannelID:
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
    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return NotificationRuleRow.id

    @override
    def entity_id_value(self) -> NotificationRuleID:
        return self.rule_id

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return row.to_data()
