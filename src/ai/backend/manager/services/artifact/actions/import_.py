import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class ImportArtifactAction(ArtifactAction):
    artifact_id: uuid.UUID
    storage_id: uuid.UUID
    bucket_name: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "import"


@dataclass
class ImportArtifactActionResult(BaseActionResult):
    result: ArtifactData
    task_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
