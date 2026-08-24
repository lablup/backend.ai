"""Update spec for the artifact_revisions table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.data.artifact.types import ArtifactRemoteStatus, ArtifactRevisionData
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater


@dataclass
class ArtifactRevisionScanUpdater(DataUpdater[ArtifactRevisionRow, ArtifactRevisionData]):
    """Write back what a scan found about a revision already recorded.

    ``remote_status`` is written only when the scan reports one: a local revision keeps
    the status it has rather than being cleared by a scan that says nothing about it.
    """

    revision_id: ArtifactRevisionID
    readme: str | None
    size: int | None
    created_at: datetime | None
    updated_at: datetime | None
    digest: str | None
    verification_result: dict[str, Any] | None
    remote_status: ArtifactRemoteStatus | None

    @property
    @override
    def row_class(self) -> type[ArtifactRevisionRow]:
        return ArtifactRevisionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ArtifactRevisionRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.revision_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {
            "readme": self.readme,
            "size": self.size,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "digest": self.digest,
            "verification_result": self.verification_result,
        }
        if self.remote_status is not None:
            to_update["remote_status"] = self.remote_status.value
        return to_update

    @override
    def to_data(self, row: ArtifactRevisionRow) -> ArtifactRevisionData:
        return row.to_dataclass()
