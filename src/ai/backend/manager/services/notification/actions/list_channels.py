from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NotificationChannelEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.row import NotificationChannelRow


@dataclass(frozen=True)
class SearchChannelsAction(
    GlobalSearcherOpsAction[NotificationChannelRow, NotificationChannelData]
):
    """Page through the notification channels."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NotificationChannelEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_notification_channels"
