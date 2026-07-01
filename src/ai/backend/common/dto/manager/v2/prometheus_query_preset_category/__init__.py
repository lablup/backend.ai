"""
Prometheus query preset category DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CategoryFilter,
    CategoryOrder,
    CreateCategoryInput,
    DeleteCategoryInput,
    SearchCategoriesInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CategoryNode,
    CreateCategoryPayload,
    DeleteCategoryPayload,
    GetCategoryPayload,
    SearchCategoriesPayload,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.types import (
    CategoryOrderField,
    OrderDirection,
)

__all__ = (
    # Types (enums)
    "OrderDirection",
    "CategoryOrderField",
    # Request (CRUD inputs)
    "CreateCategoryInput",
    "DeleteCategoryInput",
    # Request (search)
    "CategoryFilter",
    "CategoryOrder",
    "SearchCategoriesInput",
    # Response (node)
    "CategoryNode",
    # Response (CRUD payloads)
    "CreateCategoryPayload",
    "DeleteCategoryPayload",
    "GetCategoryPayload",
    # Response (search payloads)
    "SearchCategoriesPayload",
)
