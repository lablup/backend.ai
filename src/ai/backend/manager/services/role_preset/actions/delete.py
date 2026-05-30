from dataclasses import dataclass, field
from typing import override

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base.updater import BulkUpdaterError
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class BulkDeleteRolePresetsAction(RolePresetAction):
    ids: list[RolePresetID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class BulkDeleteRolePresetsActionResult(BaseActionResult):
    successes: list[RolePresetData] = field(default_factory=list)
    failures: list[BulkUpdaterError[RolePresetRow]] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
