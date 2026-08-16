from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE",
    "PrometheusQueryPresetCategoryID",
)


# Raw string mirroring the RBAC-managed EntityType.PROMETHEUS_QUERY_PRESET_CATEGORY value.
PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE = EntityType("prometheus_query_preset_category")


class PrometheusQueryPresetCategoryID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE
