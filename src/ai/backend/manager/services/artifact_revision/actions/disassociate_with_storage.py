import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class DisassociateWithStorageAction(ArtifactRevisionAction):
    artifact_revision_id: uuid.UUID
    storage_namespace_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_revision_id)

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
