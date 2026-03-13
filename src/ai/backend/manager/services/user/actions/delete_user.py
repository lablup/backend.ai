from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.user.actions.base import (
    UserSingleEntityAction,
    UserSingleEntityActionResult,
)


@dataclass
class DeleteUserAction(UserSingleEntityAction):
    email: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        # Email-based lookup - will be resolved in processor
        return self.email

    @override
    def target_element(self) -> RBACElementRef:
        # Email-based lookup requires resolution in processor
        return RBACElementRef(RBACElementType.USER, self.email)


@dataclass
class DeleteUserActionResult(UserSingleEntityActionResult):
    _user_id: str

    @override
    def entity_id(self) -> str | None:
        return self._user_id

    @override
    def target_entity_id(self) -> str:
        return self._user_id
