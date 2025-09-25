from typing import override

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityAction
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.role import SingleEntityPermissionCheckInput
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

from ...validator.single_entity import SingleEntityActionValidator


class SingleEntityActionRBACValidator(SingleEntityActionValidator):
    def __init__(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        self._repository = repository

    @override
    async def validate(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        entity_type = EntityType(action.entity_type())
        entity_id = action.target_entity_id()
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")

        await self._repository.check_permission_of_entity(
            SingleEntityPermissionCheckInput(
                user_id=user.user_id,
                operation=action.permission_operation_type(),
                target_object_id=ObjectId(
                    entity_type=entity_type,
                    entity_id=entity_id,
                ),
            )
        )
