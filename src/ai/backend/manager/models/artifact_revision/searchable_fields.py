"""What an artifact revision search can filter and order by, and how a row becomes data."""

from __future__ import annotations

import logging
from typing import override

from ai.backend.common.data.artifact.types import VerificationStepResult
from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class _ArtifactRevisionOwnFields(RowDataConverter[ArtifactRevisionRow, ArtifactRevisionData]):
    """The artifact revision's own columns."""

    field_id = SearchableField(
        ArtifactRevisionRow.id,
        UUIDConditions(ArtifactRevisionRow.id),
        ColumnOrder(ArtifactRevisionRow.id),
    )
    artifact_id = SearchableField(
        ArtifactRevisionRow.artifact_id,
        UUIDConditions(ArtifactRevisionRow.artifact_id),
        ColumnOrder(ArtifactRevisionRow.artifact_id),
    )
    version = SearchableField(
        ArtifactRevisionRow.version,
        StringConditions(ArtifactRevisionRow.version),
        ColumnOrder(ArtifactRevisionRow.version),
    )
    readme = SearchableField(
        ArtifactRevisionRow.readme,
        StringEqualityConditions(ArtifactRevisionRow.readme),
        ColumnOrder(ArtifactRevisionRow.readme),
    )
    size = SearchableField(
        ArtifactRevisionRow.size,
        IntConditions(ArtifactRevisionRow.size),
        ColumnOrder(ArtifactRevisionRow.size),
    )
    digest = SearchableField(
        ArtifactRevisionRow.digest,
        StringConditions(ArtifactRevisionRow.digest),
        ColumnOrder(ArtifactRevisionRow.digest),
    )
    status = SearchableField(
        ArtifactRevisionRow.status,
        EnumConditions(ArtifactRevisionRow.status, ArtifactStatus),
        ColumnOrder(ArtifactRevisionRow.status),
    )
    remote_status = SearchableField(
        ArtifactRevisionRow.remote_status,
        EnumConditions(ArtifactRevisionRow.remote_status, ArtifactRemoteStatus),
        ColumnOrder(ArtifactRevisionRow.remote_status),
    )
    created_at = SearchableField(
        ArtifactRevisionRow.created_at,
        DateTimeConditions(ArtifactRevisionRow.created_at),
        ColumnOrder(ArtifactRevisionRow.created_at),
    )
    updated_at = SearchableField(
        ArtifactRevisionRow.updated_at,
        DateTimeConditions(ArtifactRevisionRow.updated_at),
        ColumnOrder(ArtifactRevisionRow.updated_at),
    )
    verification_result = SearchableField(ArtifactRevisionRow.verification_result, None, None)
    """Impossible: a JSON document of the verification steps' results."""

    @override
    def to_data(self, row: ArtifactRevisionRow) -> ArtifactRevisionData:
        remote_status = self.remote_status.read(row)
        return ArtifactRevisionData(
            id=ArtifactRevisionID(self.field_id.read(row)),
            artifact_id=ArtifactID(self.artifact_id.read(row)),
            version=self.version.read(row),
            readme=self.readme.read(row),
            size=self.size.read(row),
            status=ArtifactStatus(self.status.read(row)),
            remote_status=ArtifactRemoteStatus(remote_status) if remote_status else None,
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
            digest=self.digest.read(row),
            verification_result=self._verification_result(row),
        )

    def _verification_result(self, row: ArtifactRevisionRow) -> VerificationStepResult | None:
        raw = self.verification_result.read(row)
        if raw is None:
            return None
        try:
            return VerificationStepResult.model_validate(raw)
        except Exception as e:
            log.warning(
                "Failed to validate verification_result for ArtifactRevisionRow id={}: {}",
                row.id,
                e,
            )
            return None


class ArtifactRevisionSearchableFields:
    own = _ArtifactRevisionOwnFields()
