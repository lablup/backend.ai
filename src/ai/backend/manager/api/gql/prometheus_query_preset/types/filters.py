"""Prometheus query preset GQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum

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
    gql_enum,
    gql_field,
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
    name: StringFilter | None = gql_field(description="Filter by name.", default=None)


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering query definition results.",
    ),
    name="QueryDefinitionOrderField",
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
    field: QueryDefinitionOrderField = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(
        description="Sort direction.", default=OrderDirection.DESC
    )
