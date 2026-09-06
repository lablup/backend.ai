from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.errors.auth import InsufficientPrivilege

__all__ = ("SuperAdminActionValidator",)


class SuperAdminActionValidator(GlobalActionValidator):
    """The sole gate of the global layer: the effective user must be a super admin.

    A monitor passes the reads, and nothing else: the role answers for observing the
    system, so it sees what a super admin sees and changes none of it.
    """

    @override
    async def validate(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return
        if (
            user.role == UserRole.MONITOR
            and action.operation_type() in ActionOperationType.read_operations()
        ):
            return
        raise InsufficientPrivilege("This operation requires super-admin privileges.")
