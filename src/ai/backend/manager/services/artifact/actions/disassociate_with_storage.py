import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class DisassociateWithStorageAction(ArtifactAction):
    artifact_id: uuid.UUID
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "disassociate_with_storage"


@dataclass
class DisassociateWithStorageActionResult(BaseActionResult):
    result: AssociationArtifactsStoragesData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
