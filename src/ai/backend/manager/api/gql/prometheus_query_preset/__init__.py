"""Prometheus query preset GraphQL API package."""

from .resolver import (
    admin_create_prometheus_query_preset,
    admin_delete_prometheus_query_preset,
    admin_modify_prometheus_query_preset,
    admin_prometheus_query_preset,
    admin_prometheus_query_presets,
    prometheus_query_preset_result,
)
from .types import (
    CreatePrometheusQueryPresetInput,
    CreatePrometheusQueryPresetPayload,
    DeletePrometheusQueryPresetPayload,
    MetricLabelEntryGQL,
    MetricLabelEntryInput,
    MetricResultGQL,
    MetricResultValueGQL,
    ModifyPrometheusQueryPresetInput,
    ModifyPrometheusQueryPresetPayload,
    PrometheusPresetOptionsGQL,
    PrometheusQueryPresetConnection,
    PrometheusQueryPresetEdge,
    PrometheusQueryPresetFilter,
    PrometheusQueryPresetGQL,
    PrometheusQueryPresetOrderBy,
    PrometheusQueryPresetOrderField,
    PrometheusQueryResultGQL,
    QueryTimeRangeInput,
)

__all__ = [
    # Queries
    "admin_prometheus_query_preset",
    "admin_prometheus_query_presets",
    "prometheus_query_preset_result",
    # Mutations
    "admin_create_prometheus_query_preset",
    "admin_modify_prometheus_query_preset",
    "admin_delete_prometheus_query_preset",
    # Types
    "PrometheusQueryPresetGQL",
    "PrometheusQueryPresetEdge",
    "PrometheusQueryPresetConnection",
    "PrometheusQueryPresetFilter",
    "PrometheusQueryPresetOrderBy",
    "PrometheusQueryPresetOrderField",
    "PrometheusPresetOptionsGQL",
    "MetricLabelEntryGQL",
    "MetricResultValueGQL",
    "MetricResultGQL",
    "PrometheusQueryResultGQL",
    "CreatePrometheusQueryPresetInput",
    "ModifyPrometheusQueryPresetInput",
    "QueryTimeRangeInput",
    "MetricLabelEntryInput",
    "CreatePrometheusQueryPresetPayload",
    "ModifyPrometheusQueryPresetPayload",
    "DeletePrometheusQueryPresetPayload",
]
