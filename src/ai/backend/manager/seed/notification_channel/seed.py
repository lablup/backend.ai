from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

from pydantic import Field, TypeAdapter, ValidationInfo, field_validator

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.notification import NotificationChannelType, WebhookSpec
from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.manager.models.notification.upserters import NotificationChannelUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class NotificationChannelSeed(SeedItem):
    """One ``notification_channels`` row, keyed by its stated id.

    ``spec`` is read as the model ``channel_type`` names.
    """

    id: NotificationChannelID
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    channel_type: NotificationChannelType
    spec: WebhookSpec | EmailSpec
    enabled: bool = True
    created_by: UserID

    @field_validator("spec", mode="before")
    @classmethod
    def _spec_of_channel_type(cls, value: Any, info: ValidationInfo) -> Any:
        match info.data.get("channel_type"):
            case NotificationChannelType.WEBHOOK:
                return TypeAdapter(WebhookSpec).validate_python(value)
            case NotificationChannelType.EMAIL:
                return TypeAdapter(EmailSpec).validate_python(value)
        return value

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=NotificationChannelUpserter(
                id=self.id,
                name=self.name,
                channel_type=self.channel_type,
                spec=self.spec,
                created_by=self.created_by,
                description=self.description,
                enabled=self.enabled,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        """The rule the create API applies to the name."""
        if not self.name.strip():
            return ["name is blank"]
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[NotificationChannelSeed]]) -> list[SeedRejection]:
        return []
