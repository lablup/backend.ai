from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.role import ScopePermissionCheckInput
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.errors.rbac import RBACForbidden
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

from ...validator.scope import ScopeActionValidator


class ScopeActionRBACValidator(ScopeActionValidator):
    def __init__(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        self._repository = repository

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        entity_type = EntityType(action.entity_type())
        scope_type = ScopeType(action.scope_type())
        scope_id = action.scope_id()
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")

        is_valid = await self._repository.check_permission_in_scope(
            ScopePermissionCheckInput(
                user_id=user.user_id,
                operation=action.permission_operation_type(),
                target_entity_type=entity_type,
                target_scope_id=ScopeId(
                    scope_type=scope_type,
                    scope_id=scope_id,
                ),
            )
        )
        if not is_valid:
            raise RBACForbidden(
                "User does not have permission to perform this action in the specified scope "
                f"({scope_type.value}:{scope_id})"
            )
