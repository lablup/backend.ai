from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class SearchRevisionsAction(ModelRevisionBaseAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRevisionsActionResult(BaseActionResult):
    data: list[ModelRevisionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
