import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class GetArtifactRevisionAction(ArtifactRevisionAction):
    artifact_revision_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_revision_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetArtifactRevisionActionResult(BaseActionResult):
    revision: ArtifactRevisionData

    @override
    def entity_id(self) -> Optional[str]:
        return None
