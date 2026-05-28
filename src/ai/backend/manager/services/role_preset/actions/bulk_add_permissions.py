from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.repositories.base import BulkCreator
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class BulkAddRolePermissionPresetsAction(RolePresetAction):
    bulk_creator: BulkCreator[RolePermissionPresetRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkAddRolePermissionPresetsActionResult(BaseActionResult):
    permissions: list[RolePermissionPresetData]

    @override
    def entity_id(self) -> str | None:
        return None
