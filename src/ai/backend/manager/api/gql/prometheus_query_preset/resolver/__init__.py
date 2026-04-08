"""Prometheus query preset GQL resolvers."""

from .mutation import (
    admin_create_prometheus_query_preset,
    admin_delete_prometheus_query_preset,
    admin_modify_prometheus_query_preset,
)
from .query import (
    prometheus_query_preset,
    prometheus_query_preset_result,
    prometheus_query_presets,
)

__all__ = [
    # Queries
    "prometheus_query_preset",
    "prometheus_query_presets",
    "prometheus_query_preset_result",
    # Mutations
    "admin_create_prometheus_query_preset",
    "admin_modify_prometheus_query_preset",
    "admin_delete_prometheus_query_preset",
]
