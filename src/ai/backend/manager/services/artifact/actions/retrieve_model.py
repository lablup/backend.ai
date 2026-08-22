import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class RetrieveModelAction(ArtifactAction):
    registry_id: uuid.UUID | None
    model: ModelTarget

    @override
    @classmethod
    def action_name(cls) -> str:
        return "retrieve_model"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class RetrieveModelActionResult:
    result: ArtifactDataWithRevisions
