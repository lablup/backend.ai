from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.actions.v2.field.ops import GetFieldOpsAction
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.models.artifact_revision.queriers import ArtifactRevisionQuerier
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
)


@dataclass
class GetArtifactRevisionAction(
    GetFieldOpsAction[ArtifactRevisionID, ArtifactID, ArtifactRevisionRow, ArtifactRevisionData]
):
    """Read one artifact revision."""

    artifact_revision_id: ArtifactRevisionID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_revision"

    @override
    def to_owner_lookup_action(self) -> LookupArtifactRevisionOwnerAction:
        return LookupArtifactRevisionOwnerAction(revision_id=self.artifact_revision_id)

    @override
    def to_querier(self) -> ArtifactRevisionQuerier:
        return ArtifactRevisionQuerier(revision_id=self.artifact_revision_id)
