from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "PrometheusQueryPresetCategoryEntityType",
    "PrometheusQueryPresetCategoryID",
)


class PrometheusQueryPresetCategoryEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "prometheus_query_preset_category"

    @override
    @classmethod
    def description(cls) -> str:
        return "A grouping of Prometheus query presets."


class PrometheusQueryPresetCategoryID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return PrometheusQueryPresetCategoryEntityType()
