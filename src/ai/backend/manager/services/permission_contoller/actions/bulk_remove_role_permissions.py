from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import BulkRolePermissionRemoveResultData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.purger import Purger


@dataclass
class BulkRemoveRolePermissionsAction(BaseAction):
    purgers: list[Purger[PermissionRow]]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkRemoveRolePermissionsActionResult(BaseActionResult):
    data: BulkRolePermissionRemoveResultData

    @override
    def entity_id(self) -> str | None:
        for row in self.data.successes:
            return str(row.role_id)
        return None
