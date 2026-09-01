from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.single_entity.trigger import (
    SingleEntityActionTriggerMeta,
)
from ai.backend.manager.actions.v2.single_entity.validator.base import SingleEntityActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_entity import EntityPermissionCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class VirtualEntitySingleEntityActionRBACValidator(SingleEntityActionValidator):
    """Single-entity RBAC validator resolving permissions via the virtual-entity chain."""

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
    async def validate(self, meta: SingleEntityActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        key = EntityPermissionCheckKey(
            user_id=UserID(user.user_id),
            entity=meta.entity,
        )
        permission = meta.operation_type.to_permission()
        allowed = await self._repository.check_single_entity_permission_via_virtual_entity(
            key, permission
        )
        if not allowed:
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission {permission!r} "
                f"on {meta.entity.entity_type()} {meta.entity}"
            )
