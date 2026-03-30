import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class AssociateWithStorageAction(ArtifactRevisionAction):
    artifact_revision_id: uuid.UUID
    storage_namespace_id: uuid.UUID
    storage_type: ArtifactStorageType

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT_REVISION_STORAGE_LINK

    @override
    def entity_id(self) -> str | None:
        return str(self.artifact_revision_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AssociateWithStorageActionResult(BaseActionResult):
    result: AssociationArtifactsStoragesData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
