from typing import override

from ai.backend.common.data.entity.prometheus_query_preset import (
    PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("PrometheusQueryPresetCategoryID",)


class PrometheusQueryPresetCategoryID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE
