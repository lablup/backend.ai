from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "ContainerRegistryEntityType",
    "CONTAINER_REGISTRY_SCOPE_TYPE",
    "ContainerRegistryID",
)


class ContainerRegistryEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "container_registry"

    @override
    @classmethod
    def description(cls) -> str:
        return "A registry images are pulled from."


CONTAINER_REGISTRY_SCOPE_TYPE = ScopeType(ContainerRegistryEntityType())


class ContainerRegistryID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ContainerRegistryEntityType()
