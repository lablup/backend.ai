"""SearchScope types for app-config-fragment repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.manager.data.app_config_fragment.types import AppConfigScopeType
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope


@dataclass(frozen=True)
class AppConfigFragmentSearchScope(SearchScope):
    """Pin search to a single `(scope_type, scope_id)` slice of the table."""

    scope_type: AppConfigScopeType
    scope_id: str

    def to_condition(self) -> QueryCondition:
        scope_type = self.scope_type
        scope_id = self.scope_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                AppConfigFragmentRow.scope_type == scope_type,
                AppConfigFragmentRow.scope_id == scope_id,
            )

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[str]]:
        # Scope existence (domain / user) is validated upstream by RBAC.
        return []


@dataclass(frozen=True)
class UserAppConfigSearchScope(SearchScope):
    """Pin merged-view search to a target `user_id`."""

    user_id: uuid.UUID

    def to_condition(self) -> QueryCondition:
        # Merge search joins multiple scope rows per user; the per-user
        # restriction is applied by the merge-specific SQL builder rather
        # than this generic predicate. Returning a `True` condition keeps
        # this scope BatchQuerier-compatible without double-filtering.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.true()

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[uuid.UUID]]:
        # User existence is guaranteed by RBAC authentication upstream.
        return []
