from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class PrometheusQueryPresetGlobalAction(BaseGlobalAction):
    """Base for the preset operations the service still owns."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE
