from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.errors.auth import InsufficientPrivilege

__all__ = ("SuperAdminActionValidator",)


class SuperAdminActionValidator(GlobalActionValidator):
    """The sole gate of the global layer: the effective user must be a super admin.

    Mirrors the API-layer ``superadmin_required`` middleware as defense in depth on
    the action path.
    """

    @override
    async def validate(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if not user.is_superadmin:
            raise InsufficientPrivilege("This operation requires super-admin privileges.")
