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
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    QueryDefinitionOrderField as QueryDefinitionOrderFieldDTO,
)
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
)


@strawberry.experimental.pydantic.input(
    model=QueryDefinitionFilterDTO,
    name="QueryDefinitionFilter",
    description="Added in 26.3.0. Filter input for querying query definitions.",
)
class QueryDefinitionFilter:
    name: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by name.",
    )

    def to_pydantic(self) -> QueryDefinitionFilterDTO:
        return QueryDefinitionFilterDTO(
            name=self.name.to_pydantic() if self.name else None,
        )


@strawberry.enum(
    name="QueryDefinitionOrderField",
    description="Added in 26.3.0. Fields available for ordering query definition results.",
)
class QueryDefinitionOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"


@strawberry.experimental.pydantic.input(
    model=QueryDefinitionOrderDTO,
    name="QueryDefinitionOrderBy",
    description="Added in 26.3.0. Specifies ordering for query definition results.",
)
class QueryDefinitionOrderBy:
    field: QueryDefinitionOrderField = strawberry.field(description="The field to order by.")
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description="Sort direction.",
    )

    def to_pydantic(self) -> QueryDefinitionOrderDTO:
        return QueryDefinitionOrderDTO(
            field=QueryDefinitionOrderFieldDTO(self.field.value),
            direction=OrderDirectionDTO(self.direction.value),
        )
