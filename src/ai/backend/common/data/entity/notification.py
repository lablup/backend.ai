from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "NOTIFICATION_CHANNEL_ENTITY_TYPE",
    "NOTIFICATION_RULE_ENTITY_TYPE",
    "NotificationChannelID",
    "NotificationRuleID",
)


# Raw strings mirroring the RBAC-managed EntityType values.
NOTIFICATION_CHANNEL_ENTITY_TYPE = EntityType("notification_channel")
NOTIFICATION_RULE_ENTITY_TYPE = EntityType("notification_rule")


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
