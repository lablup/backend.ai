from typing import Any, override

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.bulk import BaseBulkAction
from ai.backend.manager.actions.validator.bulk import (
    BulkActionValidator,
    BulkValidationResult,
    DeniedEntity,
)
from ai.backend.manager.data.permission.role import BulkPermissionCheckInput
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

_DENY_REASON = "permission_denied"


class BulkActionRBACValidator(BulkActionValidator):
    def __init__(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        self._repository = repository

    @classmethod
    @override
    def name(cls) -> str:
        return "rbac"

    @override
    async def validate(
        self, action: BaseBulkAction[Any], meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        user = current_user()
        if user is None:
            raise UnreachableError("User context is not available")
        entity_ids = list(action.entity_ids)
        if user.is_superadmin:
            return BulkValidationResult(
                allowed_entity_ids=entity_ids,
                denied_entities=[],
            )
        permission_map = await self._repository.check_bulk_permission_with_scope_chain(
            BulkPermissionCheckInput(
                user_id=user.user_id,
                target_element_type=action.entity_type().to_element(),
                target_entity_ids=entity_ids,
                operation=action.operation_type().to_permission_operation(),
            )
        )
        allowed_entity_ids: list[str] = []
        denied_entities: list[DeniedEntity] = []
        for eid in entity_ids:
            if permission_map.get(eid, False):
                allowed_entity_ids.append(eid)
            else:
                denied_entities.append(DeniedEntity(entity_id=eid, deny_reason=_DENY_REASON))
        return BulkValidationResult(
            allowed_entity_ids=allowed_entity_ids,
            denied_entities=denied_entities,
        )
