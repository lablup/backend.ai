"""Types for domain repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow, ScalingGroupRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    "DomainSearchScope",
    "DomainSearchResult",
)


@dataclass(frozen=True)
class DomainSearchScope(SearchScope):
    """Required scope for domain search within a resource group.

    Used for resource group-scoped queries where domains are filtered
    by their association with a scaling group.
    """

    resource_group: str
    """Required. The scaling group (resource group) to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for ScalingGroupForDomainRow."""
        resource_group = self.resource_group

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.scaling_group == resource_group

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[str]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ScalingGroupRow.name,
                value=self.resource_group,
                error=ScalingGroupNotFound(self.resource_group),
            ),
        ]


@dataclass
class DomainSearchResult:
    """Result from searching domains."""

    items: list[DomainData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
