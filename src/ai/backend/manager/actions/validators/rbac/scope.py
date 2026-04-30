from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.validator.scope import ScopeActionValidator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.permission.role import (
    PermissionResolutionKey,
    ScopeChainPermissionCheckInput,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class ScopeActionRBACValidator(ScopeActionValidator):
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

        target = action.target_element()
        allowed = await self._repository.check_permission_with_scope_chain(
            ScopeChainPermissionCheckInput(
                key=PermissionResolutionKey(
                    user_id=user.user_id,
                    element_type=target.element_type,
                    entity_id=target.element_id,
                    subject_entity_type=action.entity_type().to_element(),
                ),
                operation=action.operation_type().to_permission_operation(),
            )
        )
        if not allowed:
            raise NotEnoughPermission(
                f"User {user.user_id} lacks permission "
                f"{action.operation_type().to_permission_operation()} "
                f"on {action.entity_type()} at {action.target_element()}"
            )
