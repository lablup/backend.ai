"""Read specs for artifact revisions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class ArtifactRevisionOwnerLookup(FieldOwnerLookup[ArtifactRevisionID, ArtifactID]):
    """The artifact a revision belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[ArtifactRevisionID]
    ) -> sa.sql.Select[tuple[ArtifactRevisionID, ArtifactID]]:
        return sa.select(ArtifactRevisionRow.id, ArtifactRevisionRow.artifact_id).where(
            ArtifactRevisionRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, row: Row[Any]) -> ArtifactID:
        return ArtifactID(row[1])
