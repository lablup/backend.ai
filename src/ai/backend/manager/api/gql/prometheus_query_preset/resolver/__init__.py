"""Prometheus query preset GQL resolvers."""

from .mutation import (
    admin_create_prometheus_query_preset,
    admin_delete_prometheus_query_preset,
    admin_modify_prometheus_query_preset,
)
from .query import (
    admin_prometheus_query_preset,
    admin_prometheus_query_preset_result,
    admin_prometheus_query_presets,
)

__all__ = [
    # Queries
    "admin_prometheus_query_preset",
    "admin_prometheus_query_presets",
    "admin_prometheus_query_preset_result",
    # Mutations
    "admin_create_prometheus_query_preset",
    "admin_modify_prometheus_query_preset",
    "admin_delete_prometheus_query_preset",
]
