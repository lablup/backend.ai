from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.bulk import BulkCreateFailure
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.repositories.base import BulkCreator
from ai.backend.manager.services.role_preset.actions.base import RolePermissionPresetBulkAction


@dataclass
class BulkAddRolePermissionPresetsAction(RolePermissionPresetBulkAction):
    bulk_creator: BulkCreator[RolePermissionPresetRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkAddRolePermissionPresetsActionResult(BaseActionResult):
    successes: list[RolePermissionPresetData] = field(default_factory=list)
    failures: list[BulkCreateFailure] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
