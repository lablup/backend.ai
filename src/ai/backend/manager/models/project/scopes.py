"""Operation scopes for projects."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_SCOPE_TYPE,
    ResourceGroupID,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.virtual_entity.queries import (
    scope_membership_exists,
    user_scope_membership_exists,
)

__all__ = (
    "DomainProjectOperationScope",
    "ResourceGroupProjectOperationScope",
    "UserProjectOperationScope",
)


@dataclass(frozen=True)
class DomainProjectOperationScope(OperationScope):
    """Required scope for searching projects within a domain.

    Used for domain-scoped project search (domain admin+).
    """

    domain_id: DomainID
    """Required. The domain to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for ProjectRow.

        Groups reference their domain by name, so the domain UUID is resolved
        to the name via a scalar subquery.
        """
        domain_id = self.domain_id

        # TODO(BA-7571): drop the column term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                ProjectRow.domain_name
                == sa.select(DomainRow.name).where(DomainRow.id == domain_id).scalar_subquery(),
                scope_membership_exists(
                    DOMAIN_SCOPE_TYPE, domain_id, PROJECT_ENTITY_TYPE, ProjectRow.id
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[DomainID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=DomainRow.id,
                value=self.domain_id,
                error=DomainNotFound(str(self.domain_id)),
            ),
        ]


@dataclass(frozen=True)
class UserProjectOperationScope(OperationScope):
    """Required scope for searching projects a user is member of.

    Used for user-scoped project search (any authenticated user).
    Membership is read from the projects' virtual entities.
    """

    user_id: UserID
    """Required. The user to search projects for."""

    @override
    def to_condition(self) -> QueryCondition:
        """Membership predicate: the user is enrolled in the project's virtual
        scope."""
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_membership_exists(PROJECT_SCOPE_TYPE, ProjectRow.id, user_id)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UserID]]:
        """Return existence checks for scope validation.

        Note: User existence is typically already validated by auth layer.
        """
        return []


@dataclass(frozen=True)
class ResourceGroupProjectOperationScope(OperationScope):
    """The projects one resource group serves."""

    resource_group_id: ResourceGroupID

    @override
    def to_condition(self) -> QueryCondition:
        resource_group_id = self.resource_group_id

        # TODO(BA-7571): drop the association term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                ProjectRow.id.in_(
                    sa.select(ResourceGroupForProjectRow.group).where(
                        ResourceGroupForProjectRow.resource_group_id == resource_group_id
                    )
                ),
                scope_membership_exists(
                    RESOURCE_GROUP_SCOPE_TYPE,
                    resource_group_id,
                    PROJECT_ENTITY_TYPE,
                    ProjectRow.id,
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
