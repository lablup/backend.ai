from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.model_card.actions.base import ModelCardSingleEntityAction


@dataclass
class DeleteModelCardAction(ModelCardSingleEntityAction):
    purger: Purger[ModelCardRow]
    options: DeleteModelCardOptions

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_model_card"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteModelCardActionResult:
    id: UUID
