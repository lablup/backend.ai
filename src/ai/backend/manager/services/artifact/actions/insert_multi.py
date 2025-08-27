from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class InsertArtifactsAction(ArtifactAction):
    data: list[ArtifactDataWithRevisions]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "insert_multi"


@dataclass
class InsertArtifactsActionResult(BaseActionResult):
    result: list[ArtifactDataWithRevisions]

    @override
    def entity_id(self) -> Optional[str]:
        return None
