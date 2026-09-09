from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "NotificationChannelEntityType",
    "NotificationRuleEntityType",
    "NotificationChannelID",
    "NotificationRuleID",
)


class NotificationChannelEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "notification_channel"

    @override
    @classmethod
    def description(cls) -> str:
        return "A destination notifications are sent to."


class NotificationRuleEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "notification_rule"

    @override
    @classmethod
    def description(cls) -> str:
        return "A rule choosing which events reach a notification channel."


class NotificationChannelID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return NotificationChannelEntityType()


class NotificationRuleID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return NotificationRuleEntityType()
