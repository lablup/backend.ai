from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePresetPurgeFailure
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class BulkPurgeRolePresetsAction(RolePresetAction):
    ids: Sequence[RolePresetID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class BulkPurgeRolePresetsActionResult(BaseActionResult):
    success_count: int
    failures: list[RolePresetPurgeFailure]

    @override
    def entity_id(self) -> str | None:
        return None
