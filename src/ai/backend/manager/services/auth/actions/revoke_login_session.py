from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.login_session import LoginSessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.services.auth.actions.base import AuthGlobalAction
from ai.backend.manager.services.auth.actions.lookup_login_session_owner import (
    LookupLoginSessionOwnerAction,
)


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
class RevokeLoginSessionAction(BaseSingleFieldAction[LoginSessionID, UserID]):
    """Revoke one login session, answered for by the user it belongs to.

    The owner lookup reads that user, so who may revoke the session is decided the way
    every field operation decides it rather than by comparing ids in the service.
    """

    session_id: LoginSessionID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "revoke_login_session"

    @override
    def to_owner_lookup_action(self) -> LookupLoginSessionOwnerAction:
        return LookupLoginSessionOwnerAction(session_id=self.session_id)


@dataclass(frozen=True)
class RevokeLoginSessionActionResult:
    success: bool
