from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class ScanProjectModelCardsAction(ModelCardAction):
    project_id: UUID
    requester_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ScanProjectModelCardsActionResult(BaseActionResult):
    created_count: int
    updated_count: int
    errors: list[str] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
