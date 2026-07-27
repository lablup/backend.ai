from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import override

from ai.backend.common.data.idle_checker.types import (
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.metric.actions.base import (
    QueryMetricAction,
    QueryMetricActionResult,
)


@dataclass(frozen=True)
class SessionUtilizationCheck:
    spec: UtilizationSpec
    session_ids: Sequence[SessionId]


@dataclass(frozen=True)
class SessionUtilizationObservation:
    entry: UtilizationThresholdEntry
    value: Decimal

    @property
    def is_underutilized(self) -> bool:
        return self.value < self.entry.threshold

    def render(self) -> str:
        return (
            f"{self.entry.metric_name}={self.value:f}/{self.entry.threshold:f}"
            f"({self.entry.kernel_policy.value})"
        )


@dataclass(frozen=True)
class SessionUtilizationBatchAction(QueryMetricAction):
    checks: Sequence[SessionUtilizationCheck]
    evaluation_time: datetime

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_METRIC

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class SessionUtilizationBatchActionResult(QueryMetricActionResult):
    observations_by_check: Sequence[Mapping[SessionId, Sequence[SessionUtilizationObservation]]]

    @override
    def entity_id(self) -> str | None:
        return None
