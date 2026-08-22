"""Entity type and id of the artifacts table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ARTIFACT_ENTITY_TYPE", "ArtifactID")

ARTIFACT_ENTITY_TYPE = EntityType("artifact")


class ArtifactID(EntityIdentifier):
    """An artifact's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return ARTIFACT_ENTITY_TYPE
