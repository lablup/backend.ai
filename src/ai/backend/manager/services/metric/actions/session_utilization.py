from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.metric.actions.base import (
    QueryMetricAction,
    QueryMetricActionResult,
)


@dataclass(frozen=True)
class SessionUtilizationQuery:
    preset_id: PrometheusQueryPresetID
    session_ids: Sequence[SessionId]


@dataclass(frozen=True)
class SessionUtilizationObservation:
    preset_id: PrometheusQueryPresetID
    value: Decimal


@dataclass(frozen=True)
class QuerySessionUtilizationAction(QueryMetricAction):
    queries: Sequence[SessionUtilizationQuery]
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
class QuerySessionUtilizationActionResult(QueryMetricActionResult):
    observations_by_preset: Mapping[
        PrometheusQueryPresetID,
        Mapping[SessionId, SessionUtilizationObservation],
    ]

    @override
    def entity_id(self) -> str | None:
        return None
