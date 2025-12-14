from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, cast

from typing_extensions import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.notification.creators import NotificationChannelCreatorSpec

from .base import NotificationAction

if TYPE_CHECKING:
    from ai.backend.manager.models.notification import NotificationChannelRow


@dataclass
class CreateChannelAction(NotificationAction):
    """Action to create a notification channel."""

    creator: Creator[NotificationChannelRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_channel"

    @override
    def entity_id(self) -> Optional[str]:
        spec = cast(NotificationChannelCreatorSpec, self.creator.spec)
        return spec.name


@dataclass
class CreateChannelActionResult(BaseActionResult):
    """Result of creating a notification channel."""

    channel_data: NotificationChannelData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_data.id)
