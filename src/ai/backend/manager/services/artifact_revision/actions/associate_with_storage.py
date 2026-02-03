import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class AssociateWithStorageAction(ArtifactRevisionAction):
    artifact_revision_id: uuid.UUID
    storage_namespace_id: uuid.UUID
    storage_type: ArtifactStorageType

    @override
    def entity_id(self) -> str | None:
        return str(self.artifact_revision_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "associate_with_storage"


@dataclass
class AssociateWithStorageActionResult(BaseActionResult):
    result: AssociationArtifactsStoragesData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
