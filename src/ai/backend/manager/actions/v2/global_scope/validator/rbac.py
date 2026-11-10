from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)

__all__ = ("VirtualEntityGlobalActionRBACValidator",)


class VirtualEntityGlobalActionRBACValidator(GlobalActionValidator):
    """The gate of the global layer: the govern check for the action's entity type on
    the `global` singleton, behind the two role bypasses.

    A super admin passes everything and a monitor passes the reads, both read off the
    user role. Everyone else passes on the bits the `global` singleton grants for the
    action's entity type. The check names a type and no row, so a search delegated this
    way keeps reading every row of that type.

    With enforcement off the bypasses are the whole gate, as they were before roles
    answered here.
    """

    _repository: RbacPermissionCheckRepository
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        repository: RbacPermissionCheckRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider

    @override
    async def validate(self, action: BaseGlobalAction, meta: ActionTriggerMeta) -> None:
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
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            raise InsufficientPrivilege("This operation requires super-admin privileges.")

        user_id = UserID(user.user_id)
        key = GovernCheckKey(
            user_id=user_id,
            scope=global_entity_id(GlobalEntityName.GLOBAL),
            entity_type=action.entity_type(),
        )
        granted = await self._repository.governed_permissions([key])
        permission = action.operation_type().to_permission()
        if not granted.get(key, Permission.NONE).covers(permission):
            raise InsufficientPrivilege(
                f"User {user_id} lacks permission {permission!r} "
                f"on {action.entity_type()} in the global scope"
            )
