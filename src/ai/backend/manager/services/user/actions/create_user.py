from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import BulkUserCreateResultData, UserCreateResultData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.user.actions.base import UserAction, UserScopeAction


@dataclass
class CreateUserAction(UserScopeAction):
    creator: Creator[UserRow]
    group_ids: list[str] | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        # User creation happens within the domain scope
        # Domain is extracted from creator.values['domain_name']
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.creator.values.get("domain_name", "")

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.scope_id())


@dataclass
class CreateUserActionResult(BaseActionResult):
    data: UserCreateResultData
    _scope_type: ScopeType
    _scope_id: str

    @override
    def entity_id(self) -> str | None:
        return str(self.data.user.id)


@dataclass
class UserCreateSpec:
    """Specification for creating a single user, including group assignments."""

    creator: Creator[UserRow]
    group_ids: list[str] | None = None


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
