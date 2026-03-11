"""Prometheus query preset GraphQL API package."""

from .resolver import (
    admin_create_prometheus_query_preset,
    admin_delete_prometheus_query_preset,
    admin_modify_prometheus_query_preset,
    admin_prometheus_query_preset,
    admin_prometheus_query_preset_result,
    admin_prometheus_query_presets,
)
from .types import (
    CreateQueryDefinitionInput,
    CreateQueryDefinitionPayload,
    DeleteQueryDefinitionPayload,
    MetricLabelEntryGQL,
    MetricLabelEntryInput,
    MetricResultGQL,
    MetricResultValueGQL,
    ModifyQueryDefinitionInput,
    ModifyQueryDefinitionPayload,
    QueryDefinitionConnection,
    QueryDefinitionEdge,
    QueryDefinitionFilter,
    QueryDefinitionGQL,
    QueryDefinitionOptionsGQL,
    QueryDefinitionOrderBy,
    QueryDefinitionOrderField,
    QueryDefinitionResultGQL,
    QueryTimeRangeInput,
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
    # Types
    "QueryDefinitionGQL",
    "QueryDefinitionEdge",
    "QueryDefinitionConnection",
    "QueryDefinitionFilter",
    "QueryDefinitionOrderBy",
    "QueryDefinitionOrderField",
    "QueryDefinitionOptionsGQL",
    "MetricLabelEntryGQL",
    "MetricResultValueGQL",
    "MetricResultGQL",
    "QueryDefinitionResultGQL",
    "CreateQueryDefinitionInput",
    "ModifyQueryDefinitionInput",
    "QueryTimeRangeInput",
    "MetricLabelEntryInput",
    "CreateQueryDefinitionPayload",
    "ModifyQueryDefinitionPayload",
    "DeleteQueryDefinitionPayload",
]
