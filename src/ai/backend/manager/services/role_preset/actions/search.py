from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.role_preset.actions.base import RolePresetScopeAction


@dataclass
class SearchRolePresetsAction(RolePresetScopeAction):
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRolePresetsActionResult(BaseActionResult):
    items: list[RolePresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
