"""Delete specs for the notification catalogs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.notification import (
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
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class NotificationChannelPurger(
    GlobalEntityPurger[NotificationChannelRow, NotificationChannelData]
):
    channel_id: NotificationChannelID

    @override
    def row_class(self) -> type[NotificationChannelRow]:
        return NotificationChannelRow

    @override
    def pk_value(self) -> NotificationChannelID:
        return self.channel_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: NotificationChannelRow) -> NotificationChannelData:
        return row.to_data()


@dataclass
class NotificationRulePurger(GlobalEntityPurger[NotificationRuleRow, NotificationRuleData]):
    rule_id: NotificationRuleID

    @override
    def row_class(self) -> type[NotificationRuleRow]:
        return NotificationRuleRow

    @override
    def pk_value(self) -> NotificationRuleID:
        return self.rule_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return row.to_data()
