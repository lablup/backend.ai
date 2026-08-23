from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction, UserEntityAction


@dataclass(frozen=True)
class GlobalRevokeLoginSessionAction(AuthGlobalAction):
    """Revoke any login session, without reading who owns it."""

    session_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_revoke_login_session"


@dataclass(frozen=True)
class RevokeLoginSessionAction(UserEntityAction):
    """Revoke a login session the named user owns.

    The session row belongs to that user, so the operation is an update of the user and
    is answered for by them; the service rejects a session owned by anyone else.
    """

    session_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "revoke_login_session"


@dataclass(frozen=True)
class RevokeLoginSessionActionResult:
    success: bool
