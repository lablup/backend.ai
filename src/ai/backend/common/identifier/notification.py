from typing import override

from ai.backend.common.data.entity.notification import (
    NOTIFICATION_CHANNEL_ENTITY_TYPE,
    NOTIFICATION_RULE_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "NotificationChannelID",
    "NotificationRuleID",
)


class NotificationChannelID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_CHANNEL_ENTITY_TYPE


class NotificationRuleID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_RULE_ENTITY_TYPE
