"""Insert specs for the notification catalogs.

Both are global: a channel or a rule is system-wide configuration. The legacy path
registered each under its creator's user scope, which narrowed no read.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.notification import (
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.manager.data.notification.types import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.models.notification.row import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class NotificationChannelCreator(
    GlobalEntityCreator[NotificationChannelRow, NotificationChannelData]
):
    name: str
    channel_type: NotificationChannelType
    spec: WebhookSpec | EmailSpec
    created_by: UUID
    description: str | None = None
    enabled: bool = True

    @override
    def entity_id(self, row: NotificationChannelRow) -> NotificationChannelID:
        return NotificationChannelID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> NotificationChannelRow:
        return NotificationChannelRow(
            name=self.name,
            description=self.description,
            channel_type=str(self.channel_type),
            config=self.spec.model_dump(),
            enabled=self.enabled,
            created_by=self.created_by,
        )

    @override
    def to_data(self, row: NotificationChannelRow) -> NotificationChannelData:
        return row.to_data()


@dataclass
class NotificationRuleCreator(GlobalEntityCreator[NotificationRuleRow, NotificationRuleData]):
    name: str
    rule_type: NotificationRuleType
    channel_id: NotificationChannelID
    message_template: str
    created_by: UUID
    description: str | None = None
    enabled: bool = True

    @override
    def entity_id(self, row: NotificationRuleRow) -> NotificationRuleID:
        return NotificationRuleID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> NotificationRuleRow:
        return NotificationRuleRow(
            name=self.name,
            description=self.description,
            rule_type=str(self.rule_type),
            channel_id=self.channel_id,
            message_template=self.message_template,
            enabled=self.enabled,
            created_by=self.created_by,
        )

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return row.to_data()
