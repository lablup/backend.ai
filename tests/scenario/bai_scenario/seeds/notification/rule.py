"""Write specs for a notification rule."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.notification.creators import NotificationRuleCreator
from bai_scenario.seeds.seeder import Naming, SeedRowFrom, SeedRowFromTwo

TEMPLATE = "Session {{ session_name }} is {{ status }}"
"""A template the session.started data fills in whole."""


@dataclass(frozen=True)
class SeedRuleOf(SeedRowFromTwo[NotificationChannelData, UserData, NotificationRuleData]):
    """A rule dispatching through the channel laid before it, created by that user."""

    name_hint: str = "rule"
    rule_type: NotificationRuleType = NotificationRuleType.SESSION_STARTED
    message_template: str = TEMPLATE
    description: str | None = None
    enabled: bool = True

    @override
    def kind(self) -> str:
        return "규칙"

    @override
    def detail(self) -> str:
        parts = [f"{self.rule_type.value} 이벤트를 알린다"]
        if not self.enabled:
            parts.append("비활성")
        return ", ".join(parts)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self, name: str, first: NotificationChannelData, second: UserData
    ) -> NotificationRuleCreator:
        return NotificationRuleCreator(
            name=name,
            description=self.description,
            rule_type=self.rule_type,
            channel_id=first.id,
            message_template=self.message_template,
            enabled=self.enabled,
            created_by=second.id,
        )


@dataclass(frozen=True)
class SeedRuleOfNoChannel(SeedRowFrom[UserData, NotificationRuleData]):
    """A rule naming a channel id no row answers to. Nothing stops the write."""

    name_hint: str = "orphan-rule"

    @override
    def kind(self) -> str:
        return "규칙"

    @override
    def detail(self) -> str:
        return "없는 채널 id를 가리킨다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: UserData) -> NotificationRuleCreator:
        return NotificationRuleCreator(
            name=name,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=NotificationChannelID(uuid4()),
            message_template=TEMPLATE,
            created_by=source.id,
        )
