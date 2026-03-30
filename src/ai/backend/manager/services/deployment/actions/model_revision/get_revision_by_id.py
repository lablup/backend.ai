from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import (
    ModelRevisionData,
)
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class GetRevisionByIdAction(ModelRevisionBaseAction):
    revision_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.revision_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetRevisionByIdActionResult(BaseActionResult):
    data: ModelRevisionData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
