"""Types for app-config-fragment repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa

from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigScopeType,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope


@dataclass(frozen=True)
class AppConfigData:
    """Service-layer return type for the merged AppConfig view (BEP-1052 §5).

    `fragments` are ordered low → high merge priority (matching the policy's
    `scope_sources`). `config` is the deep-merged result, projected to `None`
    when every contributing fragment is empty.
    """

    user_id: uuid.UUID
    name: str
    fragments: Sequence[AppConfigFragmentData]
    config: Mapping[str, Any] | None


@dataclass
class AppConfigFragmentSearchResult:
    """Result from searching raw `app_config_fragments` rows."""

    items: list[AppConfigFragmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class AppConfigSearchResult:
    """Result from searching merged `AppConfig` views."""

    items: list[AppConfigData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


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
    """Pin merged-view search to a target `user_id` (BEP-1052 §5)."""

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
