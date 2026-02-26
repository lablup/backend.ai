"""Types for agent repository operations.

Contains Scope dataclasses for search operations.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    "ResourceGroupAgentSearchScope",
    "StatusAgentSearchScope",
)


@dataclass(frozen=True)
class ResourceGroupAgentSearchScope(SearchScope):
    """Required scope for searching agents within a resource group (scaling group).

    Used for listing agents assigned to a specific resource group.
    """

    scaling_group: str
    """Required. The resource group (scaling group) to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for AgentRow."""
        scaling_group = self.scaling_group

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.scaling_group == scaling_group

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[str]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ScalingGroupRow.name,
                value=self.scaling_group,
                error=ScalingGroupNotFound(self.scaling_group),
            ),
        ]


@dataclass(frozen=True)
class StatusAgentSearchScope(SearchScope):
    """Required scope for searching agents by status.

    Used for listing agents filtered by their operational status.
    """

    status: AgentStatus
    """Required. The agent status to filter by."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for AgentRow."""
        status = self.status

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status == status

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[str]]:
        """Return existence checks for scope validation."""
        return []
