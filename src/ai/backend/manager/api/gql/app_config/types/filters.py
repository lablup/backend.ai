"""AppConfig (merged view) GQL filter / order types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.app_config.request import (
    AppConfigFilter as AppConfigFilterDTO,
)
from ai.backend.common.dto.manager.v2.app_config.request import (
    AppConfigOrder as AppConfigOrderDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
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
        added_version=NEXT_RELEASE_VERSION,
        description="Filter input for querying merged AppConfigs.",
    ),
    name="AppConfigFilter",
)
class AppConfigFilterGQL(PydanticInputMixin[AppConfigFilterDTO]):
    name: StringFilter | None = gql_field(description="Filter by policy name.", default=None)
    user_id: UUIDFilter | None = gql_field(
        description="Filter by target user id (admin cross-user search only).",
        default=None,
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by the oldest contributing fragment's creation timestamp.",
        default=None,
    )
    updated_at: DateTimeFilter | None = gql_field(
        description="Filter by the latest contributing fragment's update timestamp.",
        default=None,
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering merged AppConfigs.",
    ),
    name="AppConfigOrderField",
)
class AppConfigOrderFieldGQL(StrEnum):
    USER_ID = "user_id"
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for merged AppConfig results.",
    ),
    name="AppConfigOrderBy",
)
class AppConfigOrderByGQL(PydanticInputMixin[AppConfigOrderDTO]):
    field: AppConfigOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(
        description="Sort direction.",
        default=OrderDirection.ASC,
    )
