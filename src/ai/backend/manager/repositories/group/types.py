"""Types for group repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.identifier.domain import DomainID
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.virtual_scope.queries import user_scope_membership_exists

__all__ = (
    "GroupSearchResult",
    "DomainProjectOperationScope",
    "UserProjectOperationScope",
)


@dataclass
class GroupSearchResult:
    """Result from searching groups/projects."""

    items: list[GroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class DomainProjectOperationScope(OperationScope):
    """Required scope for searching projects within a domain.

    Used for domain-scoped project search (domain admin+).
    """

    domain_id: DomainID
    """Required. The domain to search within."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for GroupRow.

        Groups reference their domain by name, so the domain UUID is resolved
        to the name via a scalar subquery.
        """
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.domain_name == (
                sa.select(DomainRow.name).where(DomainRow.id == domain_id).scalar_subquery()
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
    Membership is read from the projects' virtual scopes.
    """

    user_uuid: UUID
    """Required. The user UUID to search projects for."""

    @override
    def to_condition(self) -> QueryCondition:
        """Membership predicate: the user is enrolled in the project's virtual
        scope."""
        user_uuid = self.user_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_membership_exists(PROJECT_SCOPE_TYPE, GroupRow.id, user_uuid)

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation.

        Note: User existence is typically already validated by auth layer.
        """
        return []
