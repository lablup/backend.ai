from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class UpdateModelCardAction(ModelCardAction):
    id: UUID
    updater: Updater[ModelCardRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateModelCardActionResult(BaseActionResult):
    model_card: ModelCardData

    @override
    def entity_id(self) -> str | None:
        return str(self.model_card.id)
