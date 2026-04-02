from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.runtime_variant.actions.base import RuntimeVariantAction


@dataclass
class SearchRuntimeVariantsAction(RuntimeVariantAction):
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchRuntimeVariantsActionResult(BaseActionResult):
    items: list[RuntimeVariantData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
