import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.services.artifact.revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class DisassociateWithStorageAction(ArtifactRevisionSingleEntityAction):
    storage_namespace_id: uuid.UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disassociate_with_storage"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DisassociateWithStorageActionResult:
    result: AssociationArtifactsStoragesData
