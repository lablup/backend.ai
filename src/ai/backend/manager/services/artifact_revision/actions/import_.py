import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class ImportArtifactRevisionAction(ArtifactAction):
    artifact_revision_id: uuid.UUID
    storage_id: uuid.UUID
    bucket_name: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_revision_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "import"


@dataclass
class ImportArtifactRevisionActionResult(BaseActionResult):
    result: ArtifactRevisionData
    task_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
