from ai.backend.manager.actions.action.create import BaseCreateActionResult
from ai.backend.manager.data.permission.scope_entity_mapping import ScopeEntityMappingCreateInput
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

from .callback.create import EntityCreateActionCallback


class EntityCreateRBACCallback(EntityCreateActionCallback):
    def __init__(self, repository: PermissionControllerRepository) -> None:
        self._repository = repository

    async def callback(self, result: BaseCreateActionResult) -> None:
        input_data = ScopeEntityMappingCreateInput(
            scope_id=result.scope_id(),
            entity_id=result.entity_id(),
        )
        await self._repository.register_entity_to_scope(input_data)
