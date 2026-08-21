"""Delete specs for the notification catalogs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.notification import (
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.notification.types import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.models.notification.row import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class NotificationChannelPurger(EntityPurger[NotificationChannelRow, NotificationChannelData]):
    channel_id: NotificationChannelID

    @override
    def row_class(self) -> type[NotificationChannelRow]:
        return NotificationChannelRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return NotificationChannelRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.channel_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: NotificationChannelRow) -> NotificationChannelData:
        return row.to_data()


@dataclass
class NotificationRulePurger(EntityPurger[NotificationRuleRow, NotificationRuleData]):
    rule_id: NotificationRuleID

    @override
    def row_class(self) -> type[NotificationRuleRow]:
        return NotificationRuleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return NotificationRuleRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.rule_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return row.to_data()
