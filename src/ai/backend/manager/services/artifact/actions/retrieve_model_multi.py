import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class RetrieveModelsAction(ArtifactAction):
    registry_id: uuid.UUID | None
    models: list[ModelTarget]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "retrieve_models"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class RetrieveModelsActionResult:
    result: list[ArtifactDataWithRevisions]
