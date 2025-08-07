from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction
from ai.backend.manager.services.artifact.actions.types import ImportArtifactTarget


# TODO: Make this a batch action.
@dataclass
class ImportArtifactBatchAction(ArtifactAction):
    target: list[ImportArtifactTarget]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "import_batch"


@dataclass
class ImportArtifactBatchActionResult(BaseActionResult):
    result: list[ArtifactData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
