from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = (
    "ARTIFACT_REVISION_FIELD_TYPE",
    "ArtifactRevisionID",
)


ARTIFACT_REVISION_FIELD_TYPE = FieldType("artifact_revision")


class ArtifactRevisionID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ARTIFACT_REVISION_FIELD_TYPE
