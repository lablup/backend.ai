from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.models.artifact_revision.queriers import BulkArtifactRevisionQuerier
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupBulkArtifactRevisionOwnerAction,
)


@dataclass
class BulkGetArtifactRevisionsAction(
    PartialBulkGetFieldOpsAction[
        ArtifactRevisionID, ArtifactID, ArtifactRevisionRow, ArtifactRevisionData
    ]
):
    """Read the artifact revisions the caller named, answering for each one."""

    ids: Sequence[ArtifactRevisionID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_artifact_revisions"

    @override
    def field_ids(self) -> Sequence[ArtifactRevisionID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkArtifactRevisionOwnerAction:
        return LookupBulkArtifactRevisionOwnerAction(revision_ids=self.ids)

    @override
    def to_querier(self) -> BulkArtifactRevisionQuerier:
        return BulkArtifactRevisionQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[ArtifactRevisionID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
