"""Read specs for artifact revisions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.artifact import ARTIFACT_ENTITY_TYPE, ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class ArtifactRevisionOwnerLookup(FieldOwnerLookup[ArtifactRevisionID, ArtifactID]):
    """The artifact a revision belongs to."""

    @override
    def build_query(self, field_ids: Sequence[ArtifactRevisionID]) -> sa.sql.Select[Any]:
        return sa.select(
            ArtifactRevisionRow.id,
            ArtifactRevisionRow.artifact_id,
            sa.literal(ARTIFACT_ENTITY_TYPE),
        ).where(ArtifactRevisionRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID, owner_type: EntityType) -> ArtifactID:
        return ArtifactID(value)
