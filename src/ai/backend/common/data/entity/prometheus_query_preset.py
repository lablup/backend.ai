from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "PROMETHEUS_QUERY_PRESET_ENTITY_TYPE",
    "PrometheusQueryPresetID",
)


# Raw string mirroring the RBAC-managed EntityType.PROMETHEUS_QUERY_PRESET value.
PROMETHEUS_QUERY_PRESET_ENTITY_TYPE = EntityType("prometheus_query_preset")


class PrometheusQueryPresetID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return PROMETHEUS_QUERY_PRESET_ENTITY_TYPE
