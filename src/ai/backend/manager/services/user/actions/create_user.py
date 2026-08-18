from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.user.types import BulkUserCreateResultData, UserCreateResultData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.user.creators import UserCreateSpec

__all__ = (
    "CreateUserAction",
    "CreateUserActionResult",
    "UserCreateSpec",
    "BulkCreateUserAction",
    "BulkCreateUserActionResult",
)


@dataclass(frozen=True)
class CreateUserAction(BaseScopeAction):
    """Register a user in a domain, optionally enrolling it in projects."""

    domain_id: DomainID
    creator: Creator[UserRow]
    group_ids: list[str] | None = None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.domain_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_user"


@dataclass(frozen=True)
class CreateUserActionResult(BaseScopeActionResult):
    data: UserCreateResultData

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (UserID(self.data.user.id),)


@dataclass(frozen=True)
class BulkCreateUserAction(BaseGlobalAction):
    """Register several users at once, across domains."""

    items: list[UserCreateSpec]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_users"


@dataclass(frozen=True)
class BulkCreateUserActionResult:
    data: BulkUserCreateResultData
