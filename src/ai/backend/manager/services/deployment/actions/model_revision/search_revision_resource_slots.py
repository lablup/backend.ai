"""Action for searching resource slots of a deployment revision."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class SearchRevisionResourceSlotsAction(DeploymentGlobalAction):
    """Action to search resource slots allocated to a deployment revision."""

    revision_id: DeploymentRevisionID
    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_revision_resource_slots"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRevisionResourceSlotsActionResult:
    """Result of searching revision resource slots."""

    items: list[tuple[str, Decimal]]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
