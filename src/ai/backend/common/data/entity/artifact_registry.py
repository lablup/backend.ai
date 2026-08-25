"""Entity type and id of the artifact registries table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ARTIFACT_REGISTRY_ENTITY_TYPE", "ArtifactRegistryID")

ARTIFACT_REGISTRY_ENTITY_TYPE = EntityType("artifact_registry")


class ArtifactRegistryID(EntityIdentifier):
    """An artifact registry's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return ARTIFACT_REGISTRY_ENTITY_TYPE
