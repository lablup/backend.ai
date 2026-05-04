from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class DeleteModelCardAction(ModelCardAction):
    id: UUID
    options: DeleteModelCardOptions = field(default_factory=DeleteModelCardOptions)

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteModelCardActionResult(BaseActionResult):
    model_card: ModelCardData

    @override
    def entity_id(self) -> str | None:
        return str(self.model_card.id)
