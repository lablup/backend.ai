from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class LogoutAction(UserEntityAction):
    """End one of the named user's login sessions.

    The session row belongs to that user, so ending it is an update of the user, the
    same shape as revoking one by id.
    """

    session_token: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "logout"


@dataclass(frozen=True)
class LogoutActionResult:
    success: bool
