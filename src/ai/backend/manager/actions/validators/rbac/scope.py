from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.actions.validator.scope import ScopeActionValidator
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class ScopeActionRBACValidator(ScopeActionValidator):
    def __init__(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        self._repository = repository

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")

        await self._repository.check_permission_with_scope_chain(
            user_id=user.user_id,
            target_element_ref=action.target_element(),
            operation=action.operation_type().to_permission_operation(),
        )
