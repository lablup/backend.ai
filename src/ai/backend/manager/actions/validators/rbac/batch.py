from typing import override

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.batch import BaseBatchAction
from ai.backend.manager.actions.validator.batch import BatchActionValidator
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


class BatchActionRBACValidator(BatchActionValidator):
    def __init__(
        self,
        repository: PermissionControllerRepository,
    ) -> None:
        self._repository = repository

    @override
    async def validate(self, action: BaseBatchAction, meta: BaseActionTriggerMeta) -> None:
        # TODO: implement RBAC validation logic
        pass
