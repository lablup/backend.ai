import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class RetrieveModelsAction(ArtifactAction):
    registry_id: uuid.UUID | None
    models: list[ModelTarget]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class RetrieveModelsActionResult(BaseActionResult):
    result: list[ArtifactDataWithRevisions]

    @override
    def entity_id(self) -> str | None:
        return None
