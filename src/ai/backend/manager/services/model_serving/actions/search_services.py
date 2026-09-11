import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceSearchItem
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceScopeAction,
    ModelServiceScopeActionResult,
)


@dataclass
class SearchServicesAction(ModelServiceScopeAction):
    session_owner_id: uuid.UUID

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (UserID(self.session_owner_id),)

    conditions: list[QueryCondition] = field(default_factory=list)
    offset: int = 0
    limit: int = 20

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_services"


@dataclass
class SearchServicesActionResult(ModelServiceScopeActionResult):
    items: list[ServiceSearchItem]
    total_count: int
    offset: int
    limit: int
