from typing import override

from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("RetentionPolicyID",)


class RetentionPolicyID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RETENTION_POLICY_ENTITY_TYPE
