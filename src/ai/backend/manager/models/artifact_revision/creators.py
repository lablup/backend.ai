"""Insert spec for the artifact_revisions table."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ArtifactRevisionCreator(FieldCreator[ArtifactID, ArtifactRevisionRow, ArtifactRevisionData]):
    """Record one revision of the artifact that owns it.

    ``id`` is set only where the revision is copied from another installation and has
    to keep the id it already had.
    """

    version: str
    readme: str | None = None
    size: int | None = None
    status: ArtifactStatus = ArtifactStatus.SCANNED
    remote_status: ArtifactRemoteStatus | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    digest: str | None = None
    verification_result: dict[str, Any] | None = None
    id: uuid.UUID | None = None

    @override
    def field_id(self, row: ArtifactRevisionRow) -> ArtifactRevisionID:
        return ArtifactRevisionID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: ArtifactID) -> ArtifactRevisionRow:
        values: dict[str, Any] = {
            "artifact_id": owner_id,
            "version": self.version,
            "readme": self.readme,
            "size": self.size,
            "status": self.status.value,
            "remote_status": self.remote_status.value if self.remote_status else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "digest": self.digest,
            "verification_result": self.verification_result,
        }
        if self.id is not None:
            values["id"] = self.id
        return ArtifactRevisionRow(**values)

    @override
    def to_data(self, row: ArtifactRevisionRow) -> ArtifactRevisionData:
        return row.to_dataclass()
