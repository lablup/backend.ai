"""Action for searching resource slots of a deployment revision preset."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment_revision_preset.actions.base import (
    DeploymentRevisionPresetAction,
)


@dataclass
class SearchPresetResourceSlotsAction(DeploymentRevisionPresetAction):
    """Action to search resource slots allocated to a deployment revision preset."""

    preset_id: UUID
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return str(self.preset_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchPresetResourceSlotsActionResult(BaseActionResult):
    """Result of searching preset resource slots."""

    items: list[tuple[str, Decimal]]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
