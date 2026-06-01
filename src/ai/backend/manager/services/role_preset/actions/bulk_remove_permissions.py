from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.repositories.base.purger import BulkPurgerError
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class BulkRemoveRolePermissionPresetsAction(RolePresetAction):
    ids: Sequence[RolePermissionPresetID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkRemoveRolePermissionPresetsActionResult(BaseActionResult):
    successes: list[RolePermissionPresetData] = field(default_factory=list)
    failures: list[BulkPurgerError[RolePermissionPresetRow]] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
