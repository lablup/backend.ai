from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


@dataclass
class PrometheusQueryPresetAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PROMETHEUS_QUERY_PRESET


@dataclass
class PrometheusQueryPresetSingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PROMETHEUS_QUERY_PRESET

    @override
    def field_data(self) -> FieldData | None:
        return None


class PrometheusQueryPresetSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
