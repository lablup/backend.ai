"""GraphQL types for app config allow-list."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    AppConfigAllowListFilter as AppConfigAllowListFilterDTO,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    AppConfigAllowListOrder as AppConfigAllowListOrderDTO,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    CreateAppConfigAllowListInput as CreateAppConfigAllowListInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    CreateAppConfigAllowListPayload as CreateAppConfigAllowListPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    PurgeAppConfigAllowListPayload as PurgeAppConfigAllowListPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigScopeType,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigScopeTypeFilter as AppConfigScopeTypeFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin

__all__ = (
    "AppConfigAllowListConnection",
    "AppConfigAllowListEdge",
    "AppConfigAllowListFilterGQL",
    "AppConfigAllowListGQL",
    "AppConfigAllowListOrderByGQL",
    "AppConfigAllowListOrderFieldGQL",
    "AppConfigScopeTypeFilterGQL",
    "CreateAppConfigAllowListInputGQL",
    "CreateAppConfigAllowListPayloadGQL",
    "PurgeAppConfigAllowListPayloadGQL",
)


# ---------------------------------------------------------------------------
# Node / Edge / Connection
# ---------------------------------------------------------------------------


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="An app config allow-list entry (a per-(config_name, scope_type) write gate).",
    ),
    name="AppConfigAllowList",
)
class AppConfigAllowListGQL(PydanticNodeMixin[AppConfigAllowListNode]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node identifier for the app config allow-list entry."
    )
    config_name: str = gql_field(description="Gated config name (FK to app config definitions).")
    scope_type: AppConfigScopeType = gql_field(
        description="Scope type the entry permits writes at (public | domain | user)."
    )
    created_at: datetime = gql_field(description="Creation timestamp (UTC).")
    updated_at: datetime = gql_field(description="Last update timestamp (UTC).")


AppConfigAllowListEdge = Edge[AppConfigAllowListGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for app config allow-list records.",
    ),
)
class AppConfigAllowListConnection(Connection[AppConfigAllowListGQL]):
    count: int = gql_field(
        description="Total number of app config allow-list records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ---------------------------------------------------------------------------
# Filter / OrderBy
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for the scope_type enum field.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AppConfigScopeTypeFilter",
)
class AppConfigScopeTypeFilterGQL(PydanticInputMixin[AppConfigScopeTypeFilterDTO]):
    equals: AppConfigScopeType | None = gql_field(
        description="Exact scope type match.", default=None
    )
    in_: list[AppConfigScopeType] | None = gql_field(
        description="Match any of the provided scope types.", name="in", default=None
    )
    not_equals: AppConfigScopeType | None = gql_field(
        description="Exclude exact scope type match.", default=None
    )
    not_in: list[AppConfigScopeType] | None = gql_field(
        description="Exclude any of the provided scope types.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying app config allow-list entries.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AppConfigAllowListFilter",
)
class AppConfigAllowListFilterGQL(PydanticInputMixin[AppConfigAllowListFilterDTO]):
    config_name: StringFilter | None = gql_field(description="Filter by config name.", default=None)
    scope_type: AppConfigScopeTypeFilterGQL | None = gql_field(
        description="Filter by scope type.", default=None
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation datetime.", default=None
    )
    updated_at: DateTimeFilter | None = gql_field(
        description="Filter by last update datetime.", default=None
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering app config allow-list results.",
    ),
    name="AppConfigAllowListOrderField",
)
class AppConfigAllowListOrderFieldGQL(StrEnum):
    CONFIG_NAME = "config_name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for app config allow-list results.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AppConfigAllowListOrderBy",
)
class AppConfigAllowListOrderByGQL(PydanticInputMixin[AppConfigAllowListOrderDTO]):
    field: AppConfigAllowListOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


# ---------------------------------------------------------------------------
# Mutation inputs / payloads
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for registering a new app config allow-list entry.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="CreateAppConfigAllowListInput",
)
class CreateAppConfigAllowListInputGQL(PydanticInputMixin[CreateAppConfigAllowListInputDTO]):
    config_name: str = gql_field(description="Registered config name to gate.")
    scope_type: AppConfigScopeType = gql_field(
        description="Scope at which fragments may be written (public | domain | user)."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for app config allow-list entry creation.",
    ),
    model=CreateAppConfigAllowListPayloadDTO,
    name="CreateAppConfigAllowListPayload",
)
class CreateAppConfigAllowListPayloadGQL(PydanticOutputMixin[CreateAppConfigAllowListPayloadDTO]):
    app_config_allow_list: AppConfigAllowListGQL = gql_field(
        description="The created app config allow-list entry."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for app config allow-list entry purge.",
    ),
    model=PurgeAppConfigAllowListPayloadDTO,
    all_fields=True,
    name="PurgeAppConfigAllowListPayload",
)
class PurgeAppConfigAllowListPayloadGQL(PydanticOutputMixin[PurgeAppConfigAllowListPayloadDTO]):
    pass
