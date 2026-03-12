"""CreatorSpec implementations for artifact entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ArtifactCreatorSpec(CreatorSpec[ArtifactRow]):
    """CreatorSpec for artifact creation."""

    name: str
    type: ArtifactType
    registry_id: uuid.UUID
    registry_type: ArtifactRegistryType | str
    source_registry_id: uuid.UUID
    source_registry_type: ArtifactRegistryType | str
    readonly: bool = True
    description: str | None = None
    extra: Any | None = None

    @override
    def build_row(self) -> ArtifactRow:
        return ArtifactRow(
            name=self.name,
            type=self.type,
            registry_id=self.registry_id,
            registry_type=self.registry_type,
            source_registry_id=self.source_registry_id,
            source_registry_type=self.source_registry_type,
            readonly=self.readonly,
            description=self.description,
            extra=self.extra,
        )


@dataclass
class ArtifactRevisionCreatorSpec(CreatorSpec[ArtifactRevisionRow]):
    """CreatorSpec for artifact revision creation."""

    artifact_id: uuid.UUID
    version: str
    readme: str | None = None
    size: int | None = None
    status: ArtifactStatus = ArtifactStatus.SCANNED
    remote_status: ArtifactRemoteStatus | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    digest: str | None = None
    verification_result: dict | None = None
    id: uuid.UUID | None = None

    @override
    def build_row(self) -> ArtifactRevisionRow:
        if self.id is not None:
            return ArtifactRevisionRow(
                id=self.id,
                artifact_id=self.artifact_id,
                version=self.version,
                readme=self.readme,
                size=self.size,
                status=self.status.value,
                remote_status=self.remote_status.value if self.remote_status else None,
                created_at=self.created_at,
                updated_at=self.updated_at,
                digest=self.digest,
                verification_result=self.verification_result,
            )
        return ArtifactRevisionRow(
            artifact_id=self.artifact_id,
            version=self.version,
            readme=self.readme,
            size=self.size,
            status=self.status.value,
            remote_status=self.remote_status.value if self.remote_status else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
            digest=self.digest,
            verification_result=self.verification_result,
        )
