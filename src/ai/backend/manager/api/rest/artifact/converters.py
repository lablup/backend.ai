"""Converters between artifact data types and the common artifact DTOs."""

from __future__ import annotations

from ai.backend.common.dto.manager.artifact.response import (
    ArtifactDTO,
    ArtifactRevisionDTO,
)
from ai.backend.common.dto.manager.artifact_registry.response import (
    ArtifactDTO as ArtifactWithRevisionsListDTO,
)
from ai.backend.common.dto.manager.artifact_registry.response import (
    ArtifactRevisionDataDTO,
    ArtifactWithRevisionsDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactRemoteStatus,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRevisionData,
)


def revision_to_dto(data: ArtifactRevisionData) -> ArtifactRevisionDTO:
    return ArtifactRevisionDTO(
        id=data.id,
        artifact_id=data.artifact_id,
        version=data.version,
        size=data.size,
        status=ArtifactStatus(data.status.value),
        remote_status=(
            ArtifactRemoteStatus(data.remote_status.value) if data.remote_status else None
        ),
        created_at=data.created_at,
        updated_at=data.updated_at,
        digest=data.digest,
        verification_result=data.verification_result,
    )


def revision_to_dto_with_readme(data: ArtifactRevisionData) -> ArtifactRevisionDataDTO:
    return ArtifactRevisionDataDTO(
        **revision_to_dto(data).model_dump(),
        readme=data.readme,
    )


def artifact_to_dto(data: ArtifactData) -> ArtifactDTO:
    return ArtifactDTO(
        id=data.id,
        name=data.name,
        type=ArtifactType(data.type.value),
        description=data.description,
        registry_id=data.registry_id,
        source_registry_id=data.source_registry_id,
        registry_type=data.registry_type,
        source_registry_type=data.source_registry_type,
        availability=ArtifactAvailability(data.availability.value),
        scanned_at=data.scanned_at,
        updated_at=data.updated_at,
        readonly=data.readonly,
        extra=data.extra,
    )


def artifact_with_revisions_to_dto(data: ArtifactDataWithRevisions) -> ArtifactWithRevisionsListDTO:
    """Artifact with revisions, without readme in the revisions."""
    return ArtifactWithRevisionsListDTO(
        **artifact_to_dto(data).model_dump(),
        revisions=[revision_to_dto(rev) for rev in data.revisions],
    )


def artifact_with_revisions_and_readme_to_dto(
    data: ArtifactDataWithRevisions,
) -> ArtifactWithRevisionsDTO:
    return ArtifactWithRevisionsDTO(
        **artifact_to_dto(data).model_dump(),
        revisions=[revision_to_dto_with_readme(rev) for rev in data.revisions],
    )
