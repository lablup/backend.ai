from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import PrometheusQueryRangeResponse
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.prometheus_query_preset import ExecutePresetOptions
from ai.backend.manager.services.prometheus_query_preset.actions.base import (
    PrometheusQueryPresetAction,
)


@dataclass
class ExecutePresetAction(PrometheusQueryPresetAction):
    preset_id: UUID
    options: ExecutePresetOptions
    time_window: str | None
    time_range: QueryTimeRange | None

    @override
    def entity_id(self) -> str | None:
        return str(self.preset_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ExecutePresetActionResult(BaseActionResult):
    response: PrometheusQueryRangeResponse

    @override
    def entity_id(self) -> str | None:
        return None
