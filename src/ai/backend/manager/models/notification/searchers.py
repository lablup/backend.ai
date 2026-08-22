"""Searcher implementations for the notification repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.notification.types import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.models.notification.row import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class NotificationChannelSearcher(Searcher[NotificationChannelRow, NotificationChannelData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(NotificationChannelRow)

    @override
    def to_data(self, row: NotificationChannelRow) -> NotificationChannelData:
        return row.to_data()


@dataclass
class NotificationRuleSearcher(Searcher[NotificationRuleRow, NotificationRuleData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(NotificationRuleRow)

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return row.to_data()
