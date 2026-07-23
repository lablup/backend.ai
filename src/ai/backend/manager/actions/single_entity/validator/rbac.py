from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.types import EntityRef
from ai.backend.common.exception import UnreachableError
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.single_entity.validator.base import SingleEntityActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_scope import VirtualScopePermissionCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class VirtualScopeSingleEntityActionRBACValidator(SingleEntityActionValidator):
    """Single-entity RBAC validator resolving permissions via the virtual-scope chain."""

    _repository: PermissionControllerRepository
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        repository: PermissionControllerRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider

    @override
    async def validate(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        key = VirtualScopePermissionCheckKey(
            user_id=UserID(user.user_id),
            entity=EntityRef(
                entity_type=action.entity_type(),
                entity_id=action.entity_id(),
            ),
        )
        permission = action.required_permission()
        allowed = await self._repository.check_permission_via_virtual_scope(key, permission)
        if not allowed:
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission {permission!r} "
                f"on {action.entity_type()} {action.entity_id()}"
            )
