from typing import Any, override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.virtual_entity import OwnCheckKey
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)

__all__ = ("VirtualEntityUsedByRBACValidator",)


class VirtualEntityUsedByRBACValidator(ScopeActionValidator[ScopedSearchOpsAction[Any, Any]]):
    """Scoped-search RBAC validator: the own READ check on every entity whose use narrows
    the search. Runs after the scope validator; a superadmin passes."""

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
    async def validate(
        self, action: ScopedSearchOpsAction[Any, Any], meta: ActionTriggerMeta
    ) -> None:
        if not action.searcher.used_by:
            return
        if not self._config_provider.config.manager.rbac.enforcement_enabled:
            return
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        if user.is_superadmin:
            return

        user_id = UserID(user.user_id)
        keys = [
            OwnCheckKey(user_id=user_id, entity=used.target) for used in action.searcher.used_by
        ]
        owned = await self._repository.owned_permissions(keys)
        unreadable = [
            key.entity
            for key in keys
            if not owned.get(key, Permission.NONE).covers(Permission.READ)
        ]
        if unreadable:
            raise NotEnoughPermission(
                f"User {user_id} cannot read the used-by entities {unreadable}"
            )
