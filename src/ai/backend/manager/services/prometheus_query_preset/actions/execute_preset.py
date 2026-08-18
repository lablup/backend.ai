from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.prometheus_query_preset import ExecutePresetOptions


@dataclass
class ExecutePresetAction(BaseSingleEntityAction):
    """Run one stored preset's query."""

    preset_id: PrometheusQueryPresetID
    options: ExecutePresetOptions
    time_window: str | None
    time_range: QueryTimeRange | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "execute_prometheus_query_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id


@dataclass
class ExecutePresetActionResult(BaseActionResult):
    response: PrometheusResponse

    @override
    def entity_id(self) -> str | None:
        return None
