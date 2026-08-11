from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "NOTIFICATION_CHANNEL_ENTITY_TYPE",
    "NOTIFICATION_RULE_ENTITY_TYPE",
)


# Raw strings mirroring the RBAC-managed EntityType values.
NOTIFICATION_CHANNEL_ENTITY_TYPE = EntityType("notification_channel")
NOTIFICATION_RULE_ENTITY_TYPE = EntityType("notification_rule")
