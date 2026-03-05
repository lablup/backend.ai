from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ResourceSlotAction


@dataclass
class SearchResourceSlotTypesAction(ResourceSlotAction):
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_SLOT_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchResourceSlotTypesResult(BaseActionResult):
    items: list[ResourceSlotTypeData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
