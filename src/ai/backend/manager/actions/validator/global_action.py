from abc import ABC, abstractmethod
from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.global_action import BaseGlobalAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.auth import InsufficientPrivilege

__all__ = ("GlobalActionValidator", "SuperAdminActionValidator")


class GlobalActionValidator(ABC):
    """Validates a global action before execution.

    Bound to :class:`BaseGlobalAction`; independent of the RBAC scope-chain
    validators (a global action belongs to no scope).
    """

    @abstractmethod
    async def validate(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")


class SuperAdminActionValidator(GlobalActionValidator):
    """Authorize a global action: the effective user must be a super admin.

    A global action targets system-wide config that belongs to no RBAC scope,
    so there is nothing to resolve against the RBAC scope chain. Mirrors the
    API-layer ``superadmin_required`` middleware as defense in depth on the action
    path, and lets a monitor through the reads for the reason the v2 gate does.
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
