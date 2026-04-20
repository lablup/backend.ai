from typing import Any, override

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.batch import BaseBatchAction
from ai.backend.manager.actions.validator.batch import (
    BatchActionValidator,
    BatchValidationResult,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class BatchActionRBACValidator(BatchActionValidator):
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
        self, action: BaseBatchAction[Any], meta: BaseActionTriggerMeta
    ) -> BatchValidationResult:
        # TODO: wire this to PermissionControllerRepository.check_batch_permission_with_scope_chain().
        # Until then, every entity is treated as allowed so legacy behavior is preserved.
        return BatchValidationResult(
            allowed_entity_ids=list(action.entity_ids),
            denied_entities=[],
        )
