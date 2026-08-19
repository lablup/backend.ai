from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.services.idle_checker_assignment.actions.base import (
    IdleCheckerAssignmentSingleEntityAction,
)


@dataclass
class PurgeIdleCheckerAssignmentAction(IdleCheckerAssignmentSingleEntityAction):
    purger: RBACEntityPurger[IdleCheckerBindingRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def target_entity_id(self) -> str:
        return str(self.purger.spec.pk_value())

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            RBACElementType.IDLE_CHECKER_ASSIGNMENT,
            str(self.purger.spec.pk_value()),
        )


@dataclass
class PurgeIdleCheckerAssignmentActionResult(BaseSingleEntityActionResult):
    data: IdleCheckerAssignmentData

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)
