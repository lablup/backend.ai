from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.types import KernelId
from ai.backend.manager.clients.prometheus.metric_types import KernelLiveStatBatchResult
from ai.backend.manager.services.metric.actions.base import (
    QueryMetricAction,
    QueryMetricActionResult,
)


@dataclass(frozen=True)
class ContainerLiveStatAction(QueryMetricAction):
    kernel_ids: Sequence[KernelId]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_LIVE_STAT


@dataclass(frozen=True)
class ContainerLiveStatActionResult(QueryMetricActionResult):
    stats: KernelLiveStatBatchResult
