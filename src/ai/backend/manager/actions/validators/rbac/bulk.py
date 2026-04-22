from typing import Any, override

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.bulk import BaseBulkAction
from ai.backend.manager.actions.validator.bulk import (
    BulkActionValidator,
    BulkValidationResult,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


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
        # TODO: wire this to PermissionControllerRepository.check_bulk_permission_with_scope_chain().
        # Until then, every entity is treated as allowed so legacy behavior is preserved.
        return BulkValidationResult(
            allowed_entity_ids=list(action.entity_ids),
            denied_entities=[],
        )
