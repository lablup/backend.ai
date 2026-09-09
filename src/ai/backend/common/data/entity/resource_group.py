from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, NaturalKey, ScopeType

__all__ = (
    "ResourceGroupEntityType",
    "RESOURCE_GROUP_SCOPE_TYPE",
    "ResourceGroupID",
    "ResourceGroupName",
)


class ResourceGroupEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "resource_group"

    @override
    @classmethod
    def description(cls) -> str:
        return "A pool of agents sessions are scheduled onto."


RESOURCE_GROUP_SCOPE_TYPE = ScopeType(ResourceGroupEntityType())


class ResourceGroupID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ResourceGroupEntityType()


class ResourceGroupName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "resource_group_name"
