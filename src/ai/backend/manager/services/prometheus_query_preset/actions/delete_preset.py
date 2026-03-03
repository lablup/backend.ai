import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.prometheus_query_preset.actions.base import (
    PrometheusQueryPresetAction,
)


@dataclass
class DeletePresetAction(PrometheusQueryPresetAction):
    preset_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.preset_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeletePresetActionResult(BaseActionResult):
    deleted: bool

    @override
    def entity_id(self) -> str | None:
        return None
