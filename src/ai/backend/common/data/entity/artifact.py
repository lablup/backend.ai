"""Entity type and id of the artifacts table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ArtifactEntityType", "ArtifactID")


class ArtifactEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "artifact"

    @override
    @classmethod
    def description(cls) -> str:
        return "A model, package or image in an artifact registry."


class ArtifactID(EntityIdentifier):
    """An artifact's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return ArtifactEntityType()
