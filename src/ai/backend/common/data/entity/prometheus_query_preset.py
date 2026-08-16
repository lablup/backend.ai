from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE",
    "PROMETHEUS_QUERY_PRESET_ENTITY_TYPE",
    "PrometheusQueryPresetID",
)


# Raw string mirroring the RBAC-managed EntityType.PROMETHEUS_QUERY_PRESET value.
PROMETHEUS_QUERY_PRESET_ENTITY_TYPE = EntityType("prometheus_query_preset")
PROMETHEUS_QUERY_PRESET_CATEGORY_ENTITY_TYPE = EntityType("prometheus_query_preset_category")


class PrometheusQueryPresetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE
