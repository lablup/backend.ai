"""Prometheus query preset GQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum

import strawberry

from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    QueryDefinitionFilter as QueryDefinitionFilterDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    QueryDefinitionOrder as QueryDefinitionOrderDTO,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying query definitions.", added_version="26.3.0"
    ),
    name="QueryDefinitionFilter",
)
class QueryDefinitionFilter(PydanticInputMixin[QueryDefinitionFilterDTO]):
    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by name.",
    )


@strawberry.enum(
    name="QueryDefinitionOrderField",
    description="Added in 26.3.0. Fields available for ordering query definition results.",
)
class QueryDefinitionOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for query definition results.", added_version="26.3.0"
    ),
    name="QueryDefinitionOrderBy",
)
class QueryDefinitionOrderBy(PydanticInputMixin[QueryDefinitionOrderDTO]):
    field: QueryDefinitionOrderField = strawberry.field(description="The field to order by.")
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description="Sort direction.",
    )
