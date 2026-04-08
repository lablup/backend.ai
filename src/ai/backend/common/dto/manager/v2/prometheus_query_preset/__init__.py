"""
Prometheus query preset DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    CreateQueryDefinitionOptionsInput,
    DeleteQueryDefinitionInput,
    ExecuteQueryDefinitionInput,
    ExecuteQueryDefinitionOptionsInput,
    MetricLabelEntry,
    ModifyQueryDefinitionInput,
    ModifyQueryDefinitionOptionsInput,
    QueryDefinitionFilter,
    QueryDefinitionOrder,
    SearchQueryDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    CreateQueryDefinitionPayload,
    DeleteQueryDefinitionPayload,
    ExecuteQueryDefinitionPayload,
    GetQueryDefinitionPayload,
    ModifyQueryDefinitionPayload,
    QueryDefinitionExecuteDataInfo,
    QueryDefinitionMetricResultInfo,
    QueryDefinitionNode,
    SearchQueryDefinitionsPayload,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    MetricLabelEntryInfo,
    MetricValueInfo,
    OrderDirection,
    QueryDefinitionOptionsInfo,
    QueryDefinitionOrderField,
)

__all__ = (
    # Types (enums)
    "OrderDirection",
    "QueryDefinitionOrderField",
    # Types (sub-models)
    "QueryDefinitionOptionsInfo",
    "MetricLabelEntryInfo",
    "MetricValueInfo",
    # Request (options inputs)
    "CreateQueryDefinitionOptionsInput",
    "ModifyQueryDefinitionOptionsInput",
    "ExecuteQueryDefinitionOptionsInput",
    # Request (CRUD inputs)
    "CreateQueryDefinitionInput",
    "ModifyQueryDefinitionInput",
    "DeleteQueryDefinitionInput",
    # Request (search)
    "QueryDefinitionFilter",
    "QueryDefinitionOrder",
    "SearchQueryDefinitionsInput",
    # Request (execute supporting)
    "MetricLabelEntry",
    "ExecuteQueryDefinitionInput",
    # Response (node)
    "QueryDefinitionNode",
    # Response (CRUD payloads)
    "CreateQueryDefinitionPayload",
    "ModifyQueryDefinitionPayload",
    "DeleteQueryDefinitionPayload",
    "GetQueryDefinitionPayload",
    # Response (search payloads)
    "SearchQueryDefinitionsPayload",
    # Response (execute payloads)
    "QueryDefinitionMetricResultInfo",
    "QueryDefinitionExecuteDataInfo",
    "ExecuteQueryDefinitionPayload",
)
