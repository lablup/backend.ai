from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.services.prometheus_query_preset.actions.base import (
    PrometheusQueryPresetSingleEntityAction,
    PrometheusQueryPresetSingleEntityActionResult,
)


@dataclass
class GetPresetAction(PrometheusQueryPresetSingleEntityAction):
    preset_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.preset_id)

    @override
    def target_entity_id(self) -> str:
        return str(self.preset_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROMETHEUS_QUERY_PRESET, str(self.preset_id))

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetPresetActionResult(PrometheusQueryPresetSingleEntityActionResult):
    preset: PrometheusQueryPresetData

    @override
    def target_entity_id(self) -> str:
        return str(self.preset.id)
