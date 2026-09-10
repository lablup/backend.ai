from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ContainerRegistryEntityType",
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
        return "A registry that container images are pulled from, with the credentials to reach it."


class ContainerRegistryID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ContainerRegistryEntityType()
