"""Types for user repository operations.

Contains Scope dataclasses for search operations.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    "DomainUserSearchScope",
    "ProjectUserSearchScope",
)


@dataclass(frozen=True)
class DomainUserSearchScope(SearchScope):
    """Required scope for searching users within a domain.

    Used for domain_users query (domain admin+).
    """

    domain_name: str
    """Required. The domain to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for UserRow."""
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.domain_name == domain_name

        return inner

    @property
    def target(self) -> ScopeId:
        return ScopeId(ScopeType.DOMAIN, self.domain_name)

    @property
    def prerequisite_scopes(self) -> set[ScopeId]:
        return set()

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[str]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=DomainRow.name,
                value=self.domain_name,
                error=DomainNotFound(self.domain_name),
            ),
        ]


@dataclass(frozen=True)
class ProjectUserSearchScope(SearchScope):
    """Required scope for searching users within a project.

    Used for project_users query (project member+).
    Requires JOIN with association_groups_users table.
    """

    project_id: UUID
    """Required. The project (group) to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for AssocGroupUserRow."""
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssocGroupUserRow.group_id == project_id

        return inner

    @property
    def target(self) -> ScopeId:
        return ScopeId(ScopeType.PROJECT, str(self.project_id))

    @property
    def prerequisite_scopes(self) -> set[ScopeId]:
        return set()

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=GroupRow.id,
                value=self.project_id,
                error=ProjectNotFound(str(self.project_id)),
            ),
        ]
