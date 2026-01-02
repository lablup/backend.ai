"""CreatorSpec implementations for notification repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from typing_extensions import override

from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class NotificationChannelCreatorSpec(CreatorSpec[NotificationChannelRow]):
    """CreatorSpec for notification channel."""

    name: str
    channel_type: NotificationChannelType
    config: WebhookConfig
    created_by: UUID
    description: Optional[str] = None
    enabled: bool = True

    @override
    def build_row(self) -> NotificationChannelRow:
        return NotificationChannelRow(
            name=self.name,
            description=self.description,
            channel_type=str(self.channel_type),
            config=self.config.model_dump(),
            enabled=self.enabled,
            created_by=self.created_by,
        )


@dataclass
class NotificationRuleCreatorSpec(CreatorSpec[NotificationRuleRow]):
    """CreatorSpec for notification rule."""

    name: str
    rule_type: NotificationRuleType
    channel_id: UUID
    message_template: str
    created_by: UUID
    description: Optional[str] = None
    enabled: bool = True

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
