from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.types import EntityRef
from ai.backend.common.exception import UnreachableError
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.bulk.base import BaseBulkAction
from ai.backend.manager.actions.bulk.validator.base import BulkActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_scope import VirtualScopePermissionCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class VirtualScopeBulkActionRBACValidator(BulkActionValidator):
    """Bulk RBAC validator resolving permissions via the virtual-scope chain.

    One bulk check across all target entities; the action is rejected as a
    whole if any target lacks the required permission.
    """

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
    async def validate(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        keys = [
            VirtualScopePermissionCheckKey(
                user_id=UserID(user.user_id),
                entity=EntityRef(
                    entity_type=action.entity_type(),
                    entity_id=entity_id,
                ),
            )
            for entity_id in action.entity_ids()
        ]
        permission = action.required_permission()
        permission_map = await self._repository.check_bulk_permission_via_virtual_scope(
            keys, permission
        )
        denied = [key.entity.entity_id for key in keys if not permission_map.get(key, False)]
        if denied:
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission {permission!r} "
                f"on {action.entity_type()} entities {denied}"
            )
