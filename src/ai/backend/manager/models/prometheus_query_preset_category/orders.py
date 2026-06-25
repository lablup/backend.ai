"""Query orders for the prometheus_query_preset_category domain."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)


class PrometheusQueryPresetCategoryOrders:
    """QueryOrder factories for prometheus query preset category sorting."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PrometheusQueryPresetCategoryRow.name.asc()
        return PrometheusQueryPresetCategoryRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PrometheusQueryPresetCategoryRow.created_at.asc()
        return PrometheusQueryPresetCategoryRow.created_at.desc()
