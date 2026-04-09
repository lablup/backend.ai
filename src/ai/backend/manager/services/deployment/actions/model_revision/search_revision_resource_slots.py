"""Action for searching resource slots of a deployment revision."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class SearchRevisionResourceSlotsAction(ModelRevisionBaseAction):
    """Action to search resource slots allocated to a deployment revision."""

    revision_id: uuid.UUID
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return str(self.revision_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRevisionResourceSlotsActionResult(BaseActionResult):
    """Result of searching revision resource slots."""

    items: list[tuple[str, Decimal]]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
