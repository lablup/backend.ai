import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.services.artifact_revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
)


@dataclass
class GetDownloadPresignedURLAction(BaseSingleFieldAction[ArtifactRevisionID, ArtifactID]):
    """Hand out a URL that reads one artifact revision's object.

    Answered for by the revision: the storage is picked from the reservoir config,
    not by the caller.
    """

    artifact_revision_id: ArtifactRevisionID
    key: str
    expiration: int | None = None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_download_presigned_url"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def to_owner_lookup_action(self) -> LookupArtifactRevisionOwnerAction:
        return LookupArtifactRevisionOwnerAction(revision_id=self.artifact_revision_id)


@dataclass
class GetDownloadPresignedURLActionResult:
    storage_id: uuid.UUID
    presigned_url: str
