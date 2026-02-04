"""Types for group repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group.row import AssocGroupUserRow, GroupRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    "GroupSearchResult",
    "DomainProjectSearchScope",
    "UserProjectSearchScope",
)


@dataclass
class GroupSearchResult:
    """Result from searching groups/projects."""

    items: list[GroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class DomainProjectSearchScope(SearchScope):
    """Required scope for searching projects within a domain.

    Used for domain-scoped project search (domain admin+).
    """

    domain_name: str
    """Required. The domain to search within."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for GroupRow."""
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.domain_name == domain_name

        return inner

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
class UserProjectSearchScope(SearchScope):
    """Required scope for searching projects a user is member of.

    Used for user-scoped project search (any authenticated user).
    Requires checking association_groups_users table.
    """

    user_uuid: UUID
    """Required. The user UUID to search projects for."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for AssocGroupUserRow.

        This will be used in a JOIN query with GroupRow.
        """
        user_uuid = self.user_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssocGroupUserRow.user_id == user_uuid

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation.

        Note: User existence is typically already validated by auth layer.
        """
        return []
