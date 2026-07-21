"""Types for app config fragment repository operations (search scopes, resolve arguments)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope

__all__ = (
    "AppConfigScopeArguments",
    "ResolvedAppConfigScope",
    "DomainAppConfigFragmentSearchScope",
    "UserAppConfigFragmentSearchScope",
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
class DomainAppConfigFragmentSearchScope(SearchScope):
    """Fragments written at one domain scope (``scope_type == domain``, ``scope_id == domain_id``).

    One scope = one item of a scoped fragment query; the repository combines multiple
    scopes with ``OR``. ``existence_checks`` is empty by ``SearchableActionTarget``
    convention — RBAC already gates scope reachability.
    """

    domain_id: DomainID

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                AppConfigFragmentRow.scope_type == AppConfigScopeType.DOMAIN,
                AppConfigFragmentRow.scope_id == domain_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class UserAppConfigFragmentSearchScope(SearchScope):
    """Fragments written at one user scope (``scope_type == user``, ``scope_id == user_id``)."""

    user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                AppConfigFragmentRow.scope_type == AppConfigScopeType.USER,
                AppConfigFragmentRow.scope_id == user_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
