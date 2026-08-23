"""Operation scopes for fair share entities."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.errors.resource import (
    DomainNotFound,
    ProjectNotFound,
    ResourceGroupNotFound,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = (
    "DomainFairShareOperationScope",
    "ProjectFairShareOperationScope",
    "UserFairShareOperationScope",
)


@dataclass(frozen=True)
class DomainFairShareOperationScope(OperationScope):
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
                column=ResourceGroupRow.id,
                value=self.resource_group_id,
                error=ResourceGroupNotFound(str(self.resource_group_id)),
            ),
        ]


@dataclass(frozen=True)
class ProjectFairShareOperationScope(OperationScope):
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
        """Convert scope to a query condition for ProjectRow filtered by domain.

        The resource_group filter is applied in the LEFT JOIN condition,
        so only the domain filter is needed here.
        """
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectRow.domain_name == domain_name

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ResourceGroupRow.id,
                value=self.resource_group_id,
                error=ResourceGroupNotFound(str(self.resource_group_id)),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
        ]


@dataclass(frozen=True)
class UserFairShareOperationScope(OperationScope):
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
        """Convert scope to a query condition for ProjectRow filtered by domain and project.

        The resource_group filter is applied in the LEFT JOIN condition,
        so only domain and project filters are needed here.
        """
        domain_name = self.domain_name
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                ProjectRow.domain_name == domain_name,
                ProjectRow.id == project_id,
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
                column=ResourceGroupRow.id,
                value=self.resource_group_id,
                error=ResourceGroupNotFound(str(self.resource_group_id)),
            ),
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]
