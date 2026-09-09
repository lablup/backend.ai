"""Entity type and id of the artifact registries table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ArtifactRegistryEntityType", "ArtifactRegistryID")


class ArtifactRegistryEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "artifact_registry"

    @override
    @classmethod
    def description(cls) -> str:
        return "A source artifacts are pulled from."


class ArtifactRegistryID(EntityIdentifier):
    """An artifact registry's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return ArtifactRegistryEntityType()
