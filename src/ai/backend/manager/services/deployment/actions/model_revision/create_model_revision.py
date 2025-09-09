from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.creator import ModelRevisionCreator
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class CreateModelRevisionAction(ModelRevisionBaseAction):
    creator: ModelRevisionCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateModelRevisionActionResult(BaseActionResult):
    revision: ModelRevisionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.revision.id)
