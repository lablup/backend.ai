from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    BulkCreatorResultWithFailures,
)
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
)


@dataclass
class BulkAddRolePermissionsAction(BaseAction):
    creator: BulkCreator[PermissionRow]

    @override
    def entity_id(self) -> str | None:
        for spec in self.creator.specs:
            if isinstance(spec, PermissionCreatorSpec):
                return str(spec.role_id)
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
class BulkAddRolePermissionsActionResult(BaseActionResult):
    result: BulkCreatorResultWithFailures[PermissionRow]

    @override
    def entity_id(self) -> str | None:
        for row in self.result.successes:
            return str(row.role_id)
        return None
