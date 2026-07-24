from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.types import EntityRef, EntityType
from ai.backend.common.exception import UnreachableError
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.scope.base import BaseScopeAction
from ai.backend.manager.actions.scope.validator.base import ScopeActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_scope import VirtualScopePermissionCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class VirtualScopeScopeActionRBACValidator(ScopeActionValidator):
    """Scope-action RBAC validator resolving permissions via the virtual-scope chain.

    Each target scope is checked as an entity (reachable through its own and its
    ancestors' virtual scopes), while permission rows are matched on the
    acted-on entity type (``subject_entity_type``). Every target scope must be
    authorized for the action to pass.
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
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
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
                    entity_type=EntityType(scope.scope_type),
                    entity_id=scope.scope_id,
                ),
                subject_entity_type=action.entity_type(),
            )
            for scope in action.scope_targets()
        ]
        permission = action.required_permission()
        permission_map = await self._repository.check_bulk_permission_via_virtual_scope(
            keys, permission
        )
        denied = [key.entity for key in keys if not permission_map.get(key, False)]
        if denied:
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission {permission!r} "
                f"on {action.entity_type()} at scopes {denied}"
            )
