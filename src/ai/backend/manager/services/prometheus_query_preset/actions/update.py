from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base.updater import Updater


@dataclass
class UpdatePresetAction(BaseSingleEntityAction):
    """Retune one stored preset."""

    preset_id: PrometheusQueryPresetID
    updater: Updater[PrometheusQueryPresetRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_prometheus_query_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id


@dataclass
class UpdatePresetActionResult(BaseActionResult):
    preset: PrometheusQueryPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
