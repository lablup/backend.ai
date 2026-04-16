from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.types import KernelId
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.metric.types import KernelLiveStatBatchResult


@dataclass(frozen=True)
class QueryKernelLiveStatAction(BaseAction):
    kernel_ids: Sequence[KernelId]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_LIVE_STAT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class QueryKernelLiveStatActionResult(BaseActionResult):
    stats: KernelLiveStatBatchResult

    @override
    def entity_id(self) -> str | None:
        return None
