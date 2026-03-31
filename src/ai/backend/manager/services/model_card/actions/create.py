from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class CreateModelCardAction(ModelCardAction):
    creator: Creator[ModelCardRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateModelCardActionResult(BaseActionResult):
    model_card: ModelCardData

    @override
    def entity_id(self) -> str | None:
        return str(self.model_card.id)
