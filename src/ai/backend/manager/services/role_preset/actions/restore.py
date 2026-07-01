from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.bulk import BulkUpdateFailure
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.role_preset.actions.base import RolePresetBulkAction


@dataclass
class BulkRestoreRolePresetsAction(RolePresetBulkAction):
    updaters: list[Updater[RolePresetRow]]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkRestoreRolePresetsActionResult(BaseActionResult):
    successes: list[RolePresetData] = field(default_factory=list)
    failures: list[BulkUpdateFailure] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
