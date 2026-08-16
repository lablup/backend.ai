from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("PrometheusQueryPresetID",)


class PrometheusQueryPresetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE
