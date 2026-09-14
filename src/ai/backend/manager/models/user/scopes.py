"""Operation scopes for users."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists

__all__ = (
    "DomainUserOperationScope",
    "ProjectUserOperationScope",
)


@dataclass(frozen=True)
class DomainUserOperationScope(OperationScope):
    """Required scope for searching users within a domain.

    Used for domain_users query (domain admin+).
    """

    domain_id: DomainID
    """Required. The domain to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Membership predicate: the user is enrolled in the domain's virtual scope."""
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_membership_exists(DomainEntityType(), domain_id, UserRow.uuid)

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
class ProjectUserOperationScope(OperationScope):
    """Required scope for searching users within a project.

    Used for project_users query (project member+).
    Membership is read from the project's virtual entity.
    """

    project_id: ProjectID
    """Required. The project (group) to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Membership predicate: the user is enrolled in the project's virtual
        scope."""
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_membership_exists(ProjectEntityType(), project_id, UserRow.uuid)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[ProjectID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=ProjectRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]
