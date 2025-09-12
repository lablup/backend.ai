import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactRevisionReadme
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class GetArtifactRevisionReadmeAction(ArtifactRevisionAction):
    artifact_revision_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_revision_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_readme"


@dataclass
class GetArtifactRevisionReadmeActionResult(BaseActionResult):
    readme_data: ArtifactRevisionReadme

    @override
    def entity_id(self) -> Optional[str]:
        return None
