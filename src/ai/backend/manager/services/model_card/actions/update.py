from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.updaters import ModelCardUpdater
from ai.backend.manager.services.model_card.actions.base import ModelCardSingleEntityAction


@dataclass
class UpdateModelCardAction(ModelCardSingleEntityAction):
    updater: ModelCardUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_model_card"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateModelCardActionResult:
    model_card: ModelCardData
