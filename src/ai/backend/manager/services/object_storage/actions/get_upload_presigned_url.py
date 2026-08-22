import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
)


@dataclass
class GetUploadPresignedURLAction(BaseSingleFieldAction[ArtifactRevisionID, ArtifactID]):
    """Hand out a URL that writes into one artifact revision's object.

    UPDATE rather than GET: what goes out is the ability to write that artifact, which
    is why the readonly flag is checked. The storage is picked from the reservoir
    config, not by the caller.
    """

    artifact_revision_id: ArtifactRevisionID
    key: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_upload_presigned_url"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def to_owner_lookup_action(self) -> LookupArtifactRevisionOwnerAction:
        return LookupArtifactRevisionOwnerAction(revision_id=self.artifact_revision_id)


@dataclass
class GetUploadPresignedURLActionResult:
    storage_id: uuid.UUID
    presigned_url: str
    fields: dict[str, str]
