from __future__ import annotations

from dataclasses import dataclass
from typing import cast, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import BulkUserCreateResultData, UserCreateResultData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.user.creators import UserCreateSpec, UserCreatorSpec
from ai.backend.manager.services.user.actions.base import (
    UserAction,
    UserScopeAction,
    UserScopeActionResult,
)

__all__ = (
    "CreateUserAction",
    "CreateUserActionResult",
    "UserCreateSpec",
    "BulkCreateUserAction",
    "BulkCreateUserActionResult",
)


@dataclass
class CreateUserAction(UserScopeAction):
    creator: Creator[UserRow]  # spec: UserCreatorSpec
    _domain_id: DomainID
    group_ids: list[str] | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        # Stays on the name; the id form is target_element(), which is what RBAC reads.
        spec = cast(UserCreatorSpec, self.creator.spec)
        return spec.domain_name or ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, str(self._domain_id))


@dataclass
class CreateUserActionResult(UserScopeActionResult):
    data: UserCreateResultData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.user.id)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.data.user.domain_name or ""


@dataclass
class BulkCreateUserAction(UserAction):
    """Action for bulk creating multiple users."""

    items: list[UserCreateSpec]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class BulkCreateUserActionResult(BaseActionResult):
    """Result of bulk user creation."""

    data: BulkUserCreateResultData

    @override
    def entity_id(self) -> str | None:
        return None
