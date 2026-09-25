"""Write specs for a notification channel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.notification import NotificationChannelType, WebhookSpec
from ai.backend.common.data.notification.types import (
    EmailMessage,
    EmailSpec,
    SMTPAuth,
    SMTPConnection,
)
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.notification.creators import NotificationChannelCreator
from bai_scenario.seeds.seeder import Naming, SeedRowFrom

WEBHOOK_URL = "https://hooks.example.test/notify"
SMTP_HOST = "smtp.example.test"
SMTP_PORT = 587
FROM_EMAIL = "noreply@example.test"
TO_EMAIL = "ops@example.test"
SMTP_USERNAME = "mailer"
SMTP_PASSWORD = "scenario-smtp-password"


@dataclass(frozen=True)
class SeedWebhookChannel(SeedRowFrom[UserData, NotificationChannelData]):
    """A channel that posts to a webhook. Created by the user laid before it."""

    name_hint: str = "channel"
    description: str | None = None
    enabled: bool = True

    @override
    def kind(self) -> str:
        return "webhook 채널"

    @override
    def detail(self) -> str:
        parts = [f"{WEBHOOK_URL}로 보낸다"]
        if not self.enabled:
            parts.append("비활성")
        return ", ".join(parts)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: UserData) -> NotificationChannelCreator:
        return NotificationChannelCreator(
            name=name,
            description=self.description,
            channel_type=NotificationChannelType.WEBHOOK,
            spec=WebhookSpec(url=WEBHOOK_URL),
            enabled=self.enabled,
            created_by=source.id,
        )


@dataclass(frozen=True)
class SeedEmailChannel(SeedRowFrom[UserData, NotificationChannelData]):
    """A channel that mails through an SMTP server. Created by the user laid before it."""

    name_hint: str = "mail-channel"
    enabled: bool = True

    @override
    def kind(self) -> str:
        return "email 채널"

    @override
    def detail(self) -> str:
        parts = [f"{SMTP_HOST}를 거쳐 {TO_EMAIL}에게 보낸다"]
        if not self.enabled:
            parts.append("비활성")
        return ", ".join(parts)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: UserData) -> NotificationChannelCreator:
        return NotificationChannelCreator(
            name=name,
            channel_type=NotificationChannelType.EMAIL,
            spec=EmailSpec(
                smtp=SMTPConnection(host=SMTP_HOST, port=SMTP_PORT),
                message=EmailMessage(from_email=FROM_EMAIL, to_emails=[TO_EMAIL]),
                auth=SMTPAuth(username=SMTP_USERNAME, password=SMTP_PASSWORD),
            ),
            enabled=self.enabled,
            created_by=source.id,
        )
