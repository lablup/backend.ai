from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta
from ai.backend.manager.actions.v2.membership.validator.base import MembershipActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_entity import OwnCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)

__all__ = ("VirtualEntityMembershipActionRBACValidator",)


class VirtualEntityMembershipActionRBACValidator(MembershipActionValidator):
    """The operation's permission asked of the entity and of every scope it moves
    through. One of them lacking it refuses the run."""

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
    async def validate(self, meta: MembershipActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        keys = [
            OwnCheckKey(user_id=UserID(user.user_id), entity=entity)
            for entity in (meta.entity, *meta.scopes)
        ]
        permission = meta.operation_type.to_permission()
        owned = await self._repository.owned_permissions(keys)
        denied = [
            key.entity for key in keys if not owned.get(key, Permission.NONE).covers(permission)
        ]
        if denied:
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission {permission!r} on {denied}"
            )
