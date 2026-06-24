"""Query orders for the prometheus_query_preset domain."""

from __future__ import annotations

from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.query_types import QueryOrder


class PrometheusQueryPresetOrders:
    """QueryOrder factories for prometheus query preset sorting."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PrometheusQueryPresetRow.name.asc()
        return PrometheusQueryPresetRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PrometheusQueryPresetRow.created_at.asc()
        return PrometheusQueryPresetRow.created_at.desc()

    @staticmethod
    def rank(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PrometheusQueryPresetRow.rank.asc()
        return PrometheusQueryPresetRow.rank.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PrometheusQueryPresetRow.updated_at.asc()
        return PrometheusQueryPresetRow.updated_at.desc()
