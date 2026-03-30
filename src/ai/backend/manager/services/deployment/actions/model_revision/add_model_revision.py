from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.creator import ModelRevisionCreator
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class AddModelRevisionAction(ModelRevisionBaseAction):
    model_deployment_id: UUID
    adder: ModelRevisionCreator

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class AddModelRevisionActionResult(BaseActionResult):
    revision: ModelRevisionData

    @override
    def entity_id(self) -> str | None:
        return str(self.revision.id)
