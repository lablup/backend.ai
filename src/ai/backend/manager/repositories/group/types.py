"""Types for group repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope

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

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for GroupRow."""
        domain_name = self.domain_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.domain_name == domain_name

        return inner

    @property
    @override
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
    Filters via the association_scopes_entities table (PROJECT scope, USER
    entity).
    """

    user_uuid: UUID
    """Required. The user UUID to search projects for."""

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition on AssociationScopesEntitiesRow.

        Used as a WHERE predicate in a JOIN query with GroupRow. Applies the
        ``scope_type=PROJECT`` / ``entity_type=USER`` filters and narrows
        ``entity_id`` to this user; the JOIN side may also re-state the
        scope/entity-type filters for redundancy without affecting results.
        """
        user_uuid_str = str(self.user_uuid)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                AssociationScopesEntitiesRow.entity_id == user_uuid_str,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation.

        Note: User existence is typically already validated by auth layer.
        """
        return []
