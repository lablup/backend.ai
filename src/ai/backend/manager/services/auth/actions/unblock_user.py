from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction


@dataclass(frozen=True)
class GlobalUnblockUserAction(AuthGlobalAction):
    """Clear the failed-login block a username carries.

    The block is login state rather than a column on the user, so the operation is an
    update of what authentication holds against that name.
    """

    username: str

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
