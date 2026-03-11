from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.dto.manager.deployment.response import ModelDefinitionDTO
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class GetModelDefinitionAction(ModelRevisionBaseAction):
    deployment_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetModelDefinitionActionResult(BaseActionResult):
    model_definition: ModelDefinitionDTO

    @override
    def entity_id(self) -> str | None:
        return None
