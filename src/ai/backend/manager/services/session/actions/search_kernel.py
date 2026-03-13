from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.session.base import SessionAction


@dataclass
class SearchKernelsAction(SessionAction):
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_KERNEL

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchKernelsActionResult(BaseActionResult):
    data: list[KernelInfo]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
