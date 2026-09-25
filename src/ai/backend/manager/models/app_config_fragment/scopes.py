"""Operation scopes for app config fragments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import UserNotFound
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.user import UserRow

__all__ = (
    "AppConfigFragmentTarget",
    "PublicAppConfigFragmentTarget",
    "VisibleAppConfigFragmentTarget",
)


@dataclass(frozen=True)
class AppConfigFragmentTarget(ScopeTarget):
    """The fragments written at one scope, matching the row's ``(scope_type, scope_id)``.

    The owner is existence-checked so a search at a scope that does not exist is a 404
    rather than an empty page. RBAC cannot stand in for that: the scope validator returns
    early for superadmins and when RBAC enforcement is disabled.
    """

    owner: EntityIdentifier | None
    """The scope owner — ``None`` only for ``public``, which has no owner."""

    @override
    def scope_id(self) -> EntityIdentifier:
        owner = self.owner
        if owner is None:
            return global_entity_id(GlobalEntityName.PUBLIC)
        return owner

    @override
    def to_condition(self) -> QueryCondition:
        owner = self.owner

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            match owner:
                case DomainID():
                    return AppConfigFragmentConditions.by_domain_visibility(owner)()
                case UserID():
                    return AppConfigFragmentConditions.by_user_visibility(owner)()
                case _:
                    return AppConfigFragmentConditions.by_public_visibility()()

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        match AppConfigScopeType.of_owner(self.owner):
            case AppConfigScopeType.PUBLIC:
                return ()
            case AppConfigScopeType.DOMAIN:
                return [
                    ExistenceCheck(
                        column=DomainRow.id,
                        value=self.owner,
                        error=DomainNotFound(extra_data={"domain_id": str(self.owner)}),
                    ),
                ]
            case AppConfigScopeType.USER:
                return [
                    ExistenceCheck(
                        column=UserRow.uuid,
                        value=self.owner,
                        error=UserNotFound(extra_data={"user_id": str(self.owner)}),
                    ),
                ]


@dataclass(frozen=True)
class VisibleAppConfigFragmentTarget(ScopeTarget):
    """Everything one signed-in user may read: ``public``, their domain's, and their own.

    One scope rather than three the caller ORs together, so no call site can read the
    merge with a part of the rule missing. The read is answered for at the user: the
    domain's and the public rows are what holding that account already reaches.
    """

    user_id: UserID
    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

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
class PublicAppConfigFragmentTarget(ScopeTarget):
    """What a caller may read before signing in — ``public`` alone."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return global_entity_id(GlobalEntityName.PUBLIC)

    @override
    def to_condition(self) -> QueryCondition:
        return AppConfigFragmentConditions.by_public_visibility()

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
