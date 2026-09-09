from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "PrometheusQueryPresetEntityType",
    "PrometheusQueryPresetID",
)


class PrometheusQueryPresetEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "prometheus_query_preset"

    @override
    @classmethod
    def description(cls) -> str:
        return "A saved Prometheus query."


class PrometheusQueryPresetID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return PrometheusQueryPresetEntityType()
