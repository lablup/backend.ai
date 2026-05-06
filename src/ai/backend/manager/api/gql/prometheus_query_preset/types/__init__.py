"""Prometheus query preset GQL types."""

from .category import (
    CategoryFilterGQL,
    CategoryGQL,
    CategoryOrderByGQL,
    CategoryOrderFieldGQL,
    CreateCategoryInputGQL,
    CreateCategoryPayloadGQL,
    DeleteCategoryPayloadGQL,
)
from .filters import (
    QueryDefinitionFilter,
    QueryDefinitionOrderBy,
    QueryDefinitionOrderField,
)
from .inputs import (
    CreateQueryDefinitionInput,
    ExecuteQueryDefinitionOptionsInput,
    MetricLabelEntryInput,
    ModifyQueryDefinitionInput,
    PreviewQueryDefinitionInputGQL,
    QueryTimeRangeInput,
)
from .node import (
    CreateQueryDefinitionPayload,
    ModifyQueryDefinitionPayload,
    QueryDefinitionConnection,
    QueryDefinitionEdge,
    QueryDefinitionGQL,
)
from .payloads import (
    DeleteQueryDefinitionPayload,
    MetricLabelEntryGQL,
    MetricResultGQL,
    MetricResultValueGQL,
    QueryDefinitionOptionsGQL,
    QueryDefinitionResultGQL,
)

__all__ = [
    # Category types
    "CategoryGQL",
    "CategoryFilterGQL",
    "CategoryOrderByGQL",
    "CategoryOrderFieldGQL",
    "CreateCategoryInputGQL",
    "CreateCategoryPayloadGQL",
    "DeleteCategoryPayloadGQL",
    # Node types
    "QueryDefinitionGQL",
    "QueryDefinitionEdge",
    "QueryDefinitionConnection",
    # Filter and OrderBy
    "QueryDefinitionFilter",
    "QueryDefinitionOrderBy",
    "QueryDefinitionOrderField",
    # Input types
    "CreateQueryDefinitionInput",
    "ModifyQueryDefinitionInput",
    "QueryTimeRangeInput",
    "MetricLabelEntryInput",
    "ExecuteQueryDefinitionOptionsInput",
    "PreviewQueryDefinitionInputGQL",
    # Payload and result types
    "QueryDefinitionOptionsGQL",
    "MetricLabelEntryGQL",
    "MetricResultValueGQL",
    "MetricResultGQL",
    "QueryDefinitionResultGQL",
    "CreateQueryDefinitionPayload",
    "ModifyQueryDefinitionPayload",
    "DeleteQueryDefinitionPayload",
]
