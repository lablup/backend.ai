from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ARTIFACT_REVISION_ENTITY_TYPE",
    "ArtifactRevisionID",
)


ARTIFACT_REVISION_ENTITY_TYPE = EntityType("artifact_revision")


class ArtifactRevisionID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ARTIFACT_REVISION_ENTITY_TYPE
