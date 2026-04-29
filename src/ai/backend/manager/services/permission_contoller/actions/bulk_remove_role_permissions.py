from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.purger import (
    BulkPurgerResultWithFailures,
    Purger,
)


@dataclass
class BulkRemoveRolePermissionsAction(BaseAction):
    purgers: list[Purger[PermissionRow]]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_PERMISSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkRemoveRolePermissionsActionResult(BaseActionResult):
    result: BulkPurgerResultWithFailures[PermissionRow]

    @override
    def entity_id(self) -> str | None:
        for row in self.result.successes:
            return str(row.role_id)
        return None
