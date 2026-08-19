import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class GetDownloadPresignedURLAction(BaseSingleEntityAction):
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
    def entity_id(self) -> EntityIdentifier:
        return self.artifact_revision_id


@dataclass
class GetDownloadPresignedURLActionResult:
    storage_id: uuid.UUID
    presigned_url: str
