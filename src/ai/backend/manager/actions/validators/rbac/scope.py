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
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")

        enforcement_enabled = self._config_provider.config.manager.rbac.enforcement_enabled

        # Delegation has no legacy-path equivalent, so it must be authorized by
        # RBAC. When enforcement is disabled there is no scope-chain check to
        # gate it — fail closed for non-superadmin delegation instead of
        # silently acting on behalf of the owner.
        if (
            not enforcement_enabled
            and action.delegated_owner_id() is not None
            and not user.is_superadmin
        ):
            raise NotEnoughPermission(
                "Delegating to another user via owner_id requires RBAC "
                "enforcement to be enabled."
            )

        if not enforcement_enabled:
            return

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
