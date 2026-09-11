from typing import override

from ai.backend.common.data.entity.artifact import ArtifactEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = (
    "ArtifactRevisionFieldType",
    "ArtifactRevisionID",
)


class ArtifactRevisionFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "artifact_revision"

    @override
    @classmethod
    def description(cls) -> str:
        return "A version of an artifact, created by a registry scan and imported on its own."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return ArtifactEntityType


class ArtifactRevisionID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ArtifactRevisionFieldType()
