import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class DeleteArtifactAction(ArtifactAction):
    artifact_id: uuid.UUID
    artifact_version: str
    storage_id: uuid.UUID
    bucket_name: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteArtifactActionResult(BaseActionResult):
    artifact_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_id)
