"""AppConfigFragment GQL filter / order types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentFilter as AppConfigFragmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentOrder as AppConfigFragmentOrderDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter input for querying app-config fragments.",
    ),
    name="AppConfigFragmentFilter",
)
class AppConfigFragmentFilterGQL(PydanticInputMixin[AppConfigFragmentFilterDTO]):
    name: StringFilter | None = gql_field(description="Filter by policy name.", default=None)
    scope_id: StringFilter | None = gql_field(description="Filter by scope_id.", default=None)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering app-config fragments.",
    ),
    name="AppConfigFragmentOrderField",
)
class AppConfigFragmentOrderFieldGQL(StrEnum):
    SCOPE_TYPE = "scope_type"
    SCOPE_ID = "scope_id"
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for app-config fragment results.",
    ),
    name="AppConfigFragmentOrderBy",
)
class AppConfigFragmentOrderByGQL(PydanticInputMixin[AppConfigFragmentOrderDTO]):
    field: AppConfigFragmentOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(
        description="Sort direction.",
        default=OrderDirection.DESC,
    )
