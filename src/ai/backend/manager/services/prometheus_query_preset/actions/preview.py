from dataclasses import dataclass
from typing import override

from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.prometheus_query_preset.actions.base import (
    PrometheusQueryPresetAction,
)


@dataclass
class PreviewPresetAction(PrometheusQueryPresetAction):
    query_template: str

    @override
    def entity_id(self) -> str | None:
        return None

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
