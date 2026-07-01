"""Prometheus query preset GQL resolvers."""

from .category_mutation import (
    admin_create_prometheus_query_preset_category,
    admin_delete_prometheus_query_preset_category,
)
from .category_query import (
    prometheus_query_preset_categories,
    prometheus_query_preset_category,
)
from .mutation import (
    admin_create_prometheus_query_preset,
    admin_delete_prometheus_query_preset,
    admin_modify_prometheus_query_preset,
)
from .query import (
    admin_preview_prometheus_query_preset,
    prometheus_query_preset,
    prometheus_query_preset_result,
    prometheus_query_presets,
)

__all__ = [
    # Queries
    "prometheus_query_preset",
    "prometheus_query_presets",
    "prometheus_query_preset_result",
    "admin_preview_prometheus_query_preset",
    # Category Queries
    "prometheus_query_preset_category",
    "prometheus_query_preset_categories",
    # Mutations
    "admin_create_prometheus_query_preset",
    "admin_modify_prometheus_query_preset",
    "admin_delete_prometheus_query_preset",
    # Category Mutations
    "admin_create_prometheus_query_preset_category",
    "admin_delete_prometheus_query_preset_category",
]
