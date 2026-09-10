from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, NaturalKey

__all__ = (
    "ResourceGroupEntityType",
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
        return (
            "A pool of agents with its own scheduler, opened to the domains, projects and"
            " keypairs allowed to use it."
        )


class ResourceGroupID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ResourceGroupEntityType()


class ResourceGroupName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "resource_group_name"
