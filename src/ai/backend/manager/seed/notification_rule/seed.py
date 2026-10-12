from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.notification import NotificationChannelID, NotificationRuleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.manager.models.notification.upserters import NotificationRuleUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class NotificationRuleSeed(SeedItem):
    """One ``notification_rules`` row, keyed by its stated id."""

    id: NotificationRuleID
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    rule_type: NotificationRuleType
    channel_id: NotificationChannelID
    message_template: str = Field(max_length=65536)
    enabled: bool = True
    created_by: UserID

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=NotificationRuleUpserter(
                id=self.id,
                name=self.name,
                rule_type=self.rule_type,
                channel_id=self.channel_id,
                message_template=self.message_template,
                created_by=self.created_by,
                description=self.description,
                enabled=self.enabled,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[NotificationRuleSeed]]) -> list[SeedRejection]:
        return []
