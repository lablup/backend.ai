from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchKernelsAction(BaseAction):
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "kernel"

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"


@dataclass
class SearchKernelsActionResult(BaseActionResult):
    data: list[KernelInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
