"""Types for fair share repository operations.

Contains Scope dataclasses for search operations and entity-based result types.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.manager.errors.resource import (
    DomainNotFound,
    ProjectNotFound,
    ScalingGroupNotFound,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    # Scope types
    "DomainFairShareSearchScope",
    "ProjectFairShareSearchScope",
    "UserFairShareSearchScope",
)


# ==================== Scope Types ====================


@dataclass(frozen=True)
class DomainFairShareSearchScope(SearchScope):
    """Required scope for domain fair share entity search.

    Used for Field-level queries where resource_group is determined by parent context.
    """

    resource_group: str
    """Required. The scaling group to search within."""

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


@dataclass(frozen=True)
class ProjectFairShareSearchScope(SearchScope):
    """Required scope for project fair share entity search.

    Used for Field-level queries where resource_group and domain are determined by parent context.
    """

    resource_group: str
    """Required. The scaling group to search within."""

    domain_name: str
    """Required. The domain to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for ScalingGroupForProjectRow joined with DomainRow."""
        resource_group = self.resource_group
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                ScalingGroupForProjectRow.scaling_group == resource_group,
                DomainRow.name == domain_name,
            )

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
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
        ]


@dataclass(frozen=True)
class UserFairShareSearchScope(SearchScope):
    """Required scope for user fair share entity search.

    Used for Field-level queries where resource_group, domain, and project are determined by parent context.
    """

    resource_group: str
    """Required. The scaling group to search within."""

    domain_name: str
    """Required. The domain to search within."""

    project_id: uuid.UUID
    """Required. The project to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for ScalingGroupForProjectRow joined with DomainRow and GroupRow."""
        resource_group = self.resource_group
        domain_name = self.domain_name
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                ScalingGroupForProjectRow.scaling_group == resource_group,
                DomainRow.name == domain_name,
                GroupRow.id == project_id,
            )

        return inner

    @property
    def existence_checks(
        self,
    ) -> Sequence[ExistenceCheck[str] | ExistenceCheck[uuid.UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ScalingGroupRow.name,
                value=self.resource_group,
                error=ScalingGroupNotFound(self.resource_group),
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
