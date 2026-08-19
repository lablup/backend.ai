"""Entity type and id of the artifacts table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ARTIFACT_ENTITY_TYPE", "ArtifactID")

ARTIFACT_ENTITY_TYPE = EntityType("artifact")


class ArtifactID(EntityIdentifier):
    """An artifact's entity id."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ARTIFACT_ENTITY_TYPE
