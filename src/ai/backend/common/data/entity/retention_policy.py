from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RETENTION_POLICY_ENTITY_TYPE",
    "RetentionPolicyID",
)


# Raw string mirroring the RBAC-managed EntityType.RETENTION_POLICY value.
RETENTION_POLICY_ENTITY_TYPE = EntityType("retention_policy")


class RetentionPolicyID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return RETENTION_POLICY_ENTITY_TYPE
