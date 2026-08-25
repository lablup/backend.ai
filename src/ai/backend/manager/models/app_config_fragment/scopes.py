"""Operation scopes for app config fragments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import UserNotFound
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user import UserRow

__all__ = (
    "AppConfigFragmentOperationScope",
    "PublicAppConfigFragmentOperationScope",
    "VisibleAppConfigFragmentOperationScope",
)


@dataclass(frozen=True)
class AppConfigFragmentOperationScope(OperationScope):
    """The fragments written at one scope, matching the row's ``(scope_type, scope_id)``.

    The owner named by ``scope_id`` is existence-checked so a search at a scope that does
    not exist is a 404 rather than an empty page. RBAC cannot stand in for that: the scope
    validator returns early for superadmins and when RBAC enforcement is disabled.
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
        match self.scope_type:
            case AppConfigScopeType.PUBLIC:
                # Global scope — no owner row to check.
                return ()
            case AppConfigScopeType.DOMAIN:
                return [
                    ExistenceCheck(
                        column=DomainRow.id,
                        value=self.scope_id,
                        error=DomainNotFound(extra_data={"domain_id": str(self.scope_id)}),
                    ),
                ]
            case AppConfigScopeType.USER:
                return [
                    ExistenceCheck(
                        column=UserRow.uuid,
                        value=self.scope_id,
                        error=UserNotFound(extra_data={"user_id": str(self.scope_id)}),
                    ),
                ]


@dataclass(frozen=True)
class VisibleAppConfigFragmentOperationScope(OperationScope):
    """Everything one signed-in user may read: ``public``, their domain's, and their own.

    One scope rather than three the caller ORs together, so no call site can read the
    merge with a part of the rule missing.
    """

    user_id: UserID
    domain_id: DomainID

    @override
    def to_condition(self) -> QueryCondition:
        visibilities = [
            AppConfigFragmentConditions.by_public_visibility(),
            AppConfigFragmentConditions.by_user_visibility(self.user_id),
            AppConfigFragmentConditions.by_domain_visibility(self.domain_id),
        ]

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(*(visibility() for visibility in visibilities))

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # Both ids come from the session, and the RBAC gate already answered for them.
        return ()


@dataclass(frozen=True)
class PublicAppConfigFragmentOperationScope(OperationScope):
    """What a caller may read before signing in — ``public`` alone."""

    @override
    def to_condition(self) -> QueryCondition:
        return AppConfigFragmentConditions.by_public_visibility()

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
