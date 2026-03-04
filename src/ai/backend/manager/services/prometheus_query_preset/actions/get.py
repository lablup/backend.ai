import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.services.prometheus_query_preset.actions.base import (
    PrometheusQueryPresetAction,
)


@dataclass
class GetPresetAction(PrometheusQueryPresetAction):
    preset_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.preset_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetPresetActionResult(BaseActionResult):
    preset: PrometheusQueryPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
