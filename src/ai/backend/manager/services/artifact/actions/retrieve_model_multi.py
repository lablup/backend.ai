import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class RetrieveModelsAction(ArtifactAction):
    registry_id: Optional[uuid.UUID]
    models: list[ModelTarget]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "retrieve_model_multi"


@dataclass
class RetrieveModelsActionResult(BaseActionResult):
    result: list[ArtifactDataWithRevisions]

    @override
    def entity_id(self) -> Optional[str]:
        return None
