"""Action for searching resource slots of a deployment revision."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupDeploymentRevisionOwnerAction,
)


@dataclass
class SearchRevisionResourceSlotsAction(BaseSingleFieldAction[DeploymentRevisionID, DeploymentID]):
    """Search the resource slots of one revision, authorized against its deployment."""

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

    @override
    def to_owner_lookup_action(self) -> LookupDeploymentRevisionOwnerAction:
        return LookupDeploymentRevisionOwnerAction(revision_id=self.revision_id)


@dataclass
class SearchRevisionResourceSlotsActionResult:
    """Result of searching revision resource slots."""

    items: list[tuple[str, Decimal]]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
