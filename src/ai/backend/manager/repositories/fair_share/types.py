"""Types for fair share repository operations.

Contains Scope dataclasses for search operations and entity-based result types.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.errors.resource import (
    DomainNotFound,
    ProjectNotFound,
    ScalingGroupNotFound,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope

__all__ = (
    # Scope types
    "DomainFairShareSearchScope",
    "ProjectFairShareSearchScope",
    "UserFairShareSearchScope",
    # Entity-based search results
    "DomainFairShareEntitySearchResult",
    "ProjectFairShareEntitySearchResult",
    "UserFairShareEntitySearchResult",
)


# ==================== Scope Types ====================


@dataclass(frozen=True)
class DomainFairShareSearchScope(SearchScope):
    """Required scope for domain fair share entity search.

    Used for field-level queries where the resource group is determined by
    parent context.
    """

    resource_group_id: ResourceGroupID
    """Required. The scaling group id to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for DomainRow.

        Returns a trivial condition since all domains are included;
        the resource_group filter is applied in the LEFT JOIN condition.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.literal(True)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[ResourceGroupID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ScalingGroupRow.id,
                value=self.resource_group_id,
                error=ScalingGroupNotFound(str(self.resource_group_id)),
            ),
        ]


@dataclass(frozen=True)
class ProjectFairShareSearchScope(SearchScope):
    """Required scope for project fair share entity search.

    Used for field-level queries where the resource group and domain are
    determined by parent context.
    """

    domain_name: str
    """Required. The domain to search within."""

    resource_group_id: ResourceGroupID
    """Required. The scaling group id to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for GroupRow filtered by domain.

        The resource_group filter is applied in the LEFT JOIN condition,
        so only the domain filter is needed here.
        """
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.domain_name == domain_name

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ScalingGroupRow.id,
                value=self.resource_group_id,
                error=ScalingGroupNotFound(str(self.resource_group_id)),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
        ]


@dataclass(frozen=True)
class UserFairShareSearchScope(SearchScope):
    """Required scope for user fair share entity search.

    Used for field-level queries where the resource group, domain, and project
    are determined by parent context.
    """

    domain_name: str
    """Required. The domain to search within."""

    project_id: uuid.UUID
    """Required. The project to search within."""

    resource_group_id: ResourceGroupID
    """Required. The scaling group id to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for GroupRow filtered by domain and project.

        The resource_group filter is applied in the LEFT JOIN condition,
        so only domain and project filters are needed here.
        """
        domain_name = self.domain_name
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                GroupRow.domain_name == domain_name,
                GroupRow.id == project_id,
            )

        return inner

    @property
    @override
    def existence_checks(
        self,
    ) -> Sequence[
        ExistenceCheck[str] | ExistenceCheck[uuid.UUID] | ExistenceCheck[ResourceGroupID]
    ]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ScalingGroupRow.id,
                value=self.resource_group_id,
                error=ScalingGroupNotFound(str(self.resource_group_id)),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
            ExistenceCheck(
                column=GroupRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]


# ==================== Entity-based Search Results ====================


@dataclass(frozen=True)
class DomainFairShareEntitySearchResult:
    """Search result for entity-based domain fair share query.

    Contains domains associated with a resource group,
    regardless of whether they have fair share records.
    """

    items: list[DomainFairShareData]
    """List of domain fair share data."""

    total_count: int
    """Total number of items matching the query (before pagination)."""

    has_next_page: bool
    """Whether there are more items after the current page."""

    has_previous_page: bool
    """Whether there are items before the current page."""


@dataclass(frozen=True)
class ProjectFairShareEntitySearchResult:
    """Search result for entity-based project fair share query.

    Contains projects associated with a resource group,
    regardless of whether they have fair share records.
    """

    items: list[ProjectFairShareData]
    """List of project fair share data."""

    total_count: int
    """Total number of items matching the query (before pagination)."""

    has_next_page: bool
    """Whether there are more items after the current page."""

    has_previous_page: bool
    """Whether there are items before the current page."""


@dataclass(frozen=True)
class UserFairShareEntitySearchResult:
    """Search result for entity-based user fair share query.

    Contains users associated with a resource group,
    regardless of whether they have fair share records.
    """

    items: list[UserFairShareData]
    """List of user fair share data."""

    total_count: int
    """Total number of items matching the query (before pagination)."""

    has_next_page: bool
    """Whether there are more items after the current page."""

    has_previous_page: bool
    """Whether there are items before the current page."""
