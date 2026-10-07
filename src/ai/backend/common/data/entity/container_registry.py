from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, NaturalKey

__all__ = (
    "ContainerRegistryEntityType",
    "ContainerRegistryID",
    "ContainerRegistryName",
    "ContainerRegistryProjectName",
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


class ContainerRegistryName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "container_registry_name"


class ContainerRegistryProjectName(NaturalKey):
    """A project name inside a container registry, not a Backend.AI project."""

    @override
    @classmethod
    def key_name(cls) -> str:
        return "container_registry_project_name"
