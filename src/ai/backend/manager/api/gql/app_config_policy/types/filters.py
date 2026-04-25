"""AppConfigPolicy GQL filter / order types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AppConfigPolicyFilter as AppConfigPolicyFilterDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AppConfigPolicyOrder as AppConfigPolicyOrderDTO,
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
        description="Filter input for querying app-config policies.",
    ),
    name="AppConfigPolicyFilter",
)
class AppConfigPolicyFilterGQL(PydanticInputMixin[AppConfigPolicyFilterDTO]):
    config_name: StringFilter | None = gql_field(
        description="Filter by config_name.",
        default=None,
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering app-config policies.",
    ),
    name="AppConfigPolicyOrderField",
)
class AppConfigPolicyOrderFieldGQL(StrEnum):
    CONFIG_NAME = "config_name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for app-config policy results.",
    ),
    name="AppConfigPolicyOrderBy",
)
class AppConfigPolicyOrderByGQL(PydanticInputMixin[AppConfigPolicyOrderDTO]):
    field: AppConfigPolicyOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(
        description="Sort direction.",
        default=OrderDirection.DESC,
    )
