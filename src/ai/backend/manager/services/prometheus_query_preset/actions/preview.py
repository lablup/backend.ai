from dataclasses import dataclass
from typing import override

from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.prometheus_query_preset.actions.base import (
    PrometheusQueryPresetGlobalAction,
)


@dataclass
class PreviewPresetAction(PrometheusQueryPresetGlobalAction):
    query_template: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "preview_prometheus_query_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class PreviewPresetActionResult(BaseActionResult):
    response: PrometheusResponse

    @override
    def entity_id(self) -> str | None:
        return None
