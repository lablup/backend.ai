from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class ScanProjectModelCardsAction(ModelCardAction):
    project_id: UUID
    requester_id: UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scan_project_model_cards"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ScanProjectModelCardsActionResult:
    created_count: int
    updated_count: int
    errors: list[str] = field(default_factory=list)
