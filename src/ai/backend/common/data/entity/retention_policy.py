from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RetentionPolicyEntityType",
    "RetentionPolicyID",
)


class RetentionPolicyEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "retention_policy"

    @override
    @classmethod
    def description(cls) -> str:
        return "A rule purging records older than a retention period."


class RetentionPolicyID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return RetentionPolicyEntityType()
