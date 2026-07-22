"""Types for app config fragment repository operations (search scopes, resolve arguments)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope

__all__ = (
    "AppConfigFragmentSearchScope",
    "AppConfigScopeArguments",
    "ResolvedAppConfigScope",
)


@dataclass(frozen=True)
class AppConfigScopeArguments:
    """The scope arguments a caller supplies for a resolve — the domain, never the user.

    Add new caller-supplied scope dimensions here rather than growing method signatures.
    """

    domain_id: DomainID


@dataclass(frozen=True)
class ResolvedAppConfigScope:
    """The principal an ``AppConfig`` is resolved for: the resolving user and its domain.

    :class:`AppConfigScopeArguments` plus the session user. Plain value object — not a
    :class:`SearchScope`.
    """

    domain_id: DomainID
    user_id: UserID


@dataclass(frozen=True)
class AppConfigFragmentSearchScope(SearchScope):
    """The fragments written at one scope, matching the row's ``(scope_type, scope_id)``.

    ``existence_checks`` is empty: RBAC already gates whether the caller can reach the
    scope, so a missing owner is indistinguishable from an unreachable one.
    """

    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeID | None
    """The scope owner — ``None`` only for ``public``, which has no owner."""

    @override
    def to_condition(self) -> QueryCondition:
        scope_type = self.scope_type
        scope_id = self.scope_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                AppConfigFragmentRow.scope_type == scope_type,
                AppConfigFragmentRow.scope_id.is_(None)
                if scope_id is None
                else AppConfigFragmentRow.scope_id == scope_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
