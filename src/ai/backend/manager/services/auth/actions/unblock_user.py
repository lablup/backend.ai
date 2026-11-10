from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class GlobalUnblockUserAction(BaseGlobalAction):
    """Clear the failed-login block a username carries.

    The block is login state rather than a column on the user, so the operation is an
    update of what authentication holds against that name.
    """

    username: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_unblock_user"


@dataclass(frozen=True)
class GlobalUnblockUserActionResult:
    success: bool
