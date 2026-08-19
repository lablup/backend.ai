import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.services.artifact_revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class AssociateWithStorageAction(ArtifactRevisionSingleEntityAction):
    storage_namespace_id: uuid.UUID
    storage_type: ArtifactStorageType

    @override
    @classmethod
    def action_name(cls) -> str:
        return "associate_with_storage"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AssociateWithStorageActionResult:
    result: AssociationArtifactsStoragesData
