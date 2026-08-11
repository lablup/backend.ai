from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.prometheus_query_preset.actions.base import (
    PrometheusQueryPresetGlobalAction,
)


@dataclass
class ModifyPresetAction(PrometheusQueryPresetGlobalAction):
    preset_id: UUID
    updater: Updater[PrometheusQueryPresetRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "modify_prometheus_query_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ModifyPresetActionResult(BaseActionResult):
    preset: PrometheusQueryPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
