from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.types import EntityIdentifier, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta
from ai.backend.manager.actions.v2.relation.validator.base import RelationActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_scope import EntityPermissionCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

__all__ = ("VirtualScopeRelationActionRBACValidator",)


class VirtualScopeRelationActionRBACValidator(RelationActionValidator):
    """The operation's permission asked of every scope the run names, as an entity.

    Asked of the scope itself rather than of a type within it: the action declares no
    entity type, because what it writes is not an entity. One scope lacking the
    permission refuses the whole run — you must be able to touch both to relate them.
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
    async def validate(self, meta: RelationActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        entities: list[EntityIdentifier] = [
            RuntimeEntityID(scope.scope_type, scope.scope_id) for scope in meta.scope_targets
        ]
        keys = [
            EntityPermissionCheckKey(user_id=UserID(user.user_id), entity=entity)
            for entity in entities
        ]
        permission = meta.operation_type.to_permission()
        permission_map = await self._repository.check_bulk_permission_via_virtual_scope(
            keys, permission
        )
        denied = [key.entity for key in keys if not permission_map.get(key, False)]
        if denied:
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission {permission!r} on scopes {denied}"
            )
