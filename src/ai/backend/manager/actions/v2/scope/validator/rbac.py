from typing import Any, override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey, OwnCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)


class VirtualEntityScopeActionRBACValidator(ScopeActionValidator):
    """Scope-action RBAC validator: the govern check on every scope the action names and
    the own READ check on every entity whose use narrows a search, answered in one read.

    Each target scope is checked as an entity (reachable through its own and its
    ancestors' virtual entities), while permission rows are matched on the
    acted-on entity type (``entity_type``). Every target scope must be
    authorized, and every using entity readable, for the action to pass.
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
    async def validate(self, action: BaseScopeAction, meta: ActionTriggerMeta) -> None:
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return

        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        user_id = UserID(user.user_id)
        govern_keys = self._govern_keys(action, user_id)
        own_keys = self._own_keys(action, user_id)
        answered = await self._repository.checked_permissions(govern_keys, own_keys)

        permission = action.operation_type().to_permission()
        denied = [
            key.scope
            for key in govern_keys
            if not answered.governed.get(key, Permission.NONE).covers(permission)
        ]
        if denied:
            raise NotEnoughPermission(
                f"User {user_id} lacks permission {permission!r} "
                f"on {action.entity_type()} at scopes {denied}"
            )
        unreadable = [
            key.entity
            for key in own_keys
            if not answered.owned.get(key, Permission.NONE).covers(Permission.READ)
        ]
        if unreadable:
            raise NotEnoughPermission(
                f"User {user_id} cannot read the used-by entities {unreadable}"
            )

    def _govern_keys(self, action: BaseScopeAction, user_id: UserID) -> list[GovernCheckKey]:
        return [
            GovernCheckKey(user_id=user_id, scope=scope, entity_type=action.entity_type())
            for scope in action.scope_targets()
        ]

    def _own_keys(self, action: BaseScopeAction, user_id: UserID) -> list[OwnCheckKey]:
        """The entities a scoped search names as uses; every other scope action names none."""
        if not isinstance(action, ScopedSearchOpsAction):
            return []
        search_action: ScopedSearchOpsAction[Any, Any] = action
        return [
            OwnCheckKey(user_id=user_id, entity=used.target)
            for used in search_action.searcher.used_by
        ]
