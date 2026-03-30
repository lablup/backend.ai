from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ResourcePresetAction


@dataclass
class SearchResourcePresetsV2Action(ResourcePresetAction):
    """Action to search resource presets with filter/order/pagination."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchResourcePresetsV2ActionResult(BaseActionResult):
    """Result of searching resource presets."""

    presets: list[ResourcePresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
