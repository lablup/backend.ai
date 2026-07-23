"""GraphQL types for app config fragments."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, cast, override
from uuid import UUID

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentFilter as AppConfigFragmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentOrder as AppConfigFragmentOrderDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentScope as AppConfigFragmentScopeDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentNode,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigScopeTypeFilter as AppConfigScopeTypeFilterDTO,
)
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
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
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "AppConfigFragmentConnection",
    "AppConfigFragmentEdge",
    "AppConfigFragmentFilterGQL",
    "AppConfigFragmentGQL",
    "AppConfigFragmentOrderByGQL",
    "AppConfigFragmentOrderFieldGQL",
    "AppConfigFragmentScopeGQL",
    "AppConfigScopeTypeFilterGQL",
)


# ---------------------------------------------------------------------------
# Node / Edge / Connection
# ---------------------------------------------------------------------------


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One config document written at a single scope, merged by rank at resolve time.",
    ),
    name="AppConfigFragment",
)
class AppConfigFragmentGQL(PydanticNodeMixin[AppConfigFragmentNode]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node identifier for the app config fragment."
    )
    config_name: str = gql_field(description="Config name the fragment belongs to.")
    scope_type: AppConfigScopeType = gql_field(
        description="Scope the fragment is written at (public | domain | user)."
    )
    scope_id: UUID | None = gql_field(
        description="Scope identifier: the domain id or user id; null for public scope."
    )
    config: JSON = gql_field(description="The fragment's JSON config document.")
    created_at: datetime = gql_field(description="Creation timestamp (UTC).")
    updated_at: datetime = gql_field(description="Last update timestamp (UTC).")

    @classmethod
    @override
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.app_config_fragment_loader.load_many([
            AppConfigFragmentID(UUID(nid)) for nid in node_ids
        ])
        return cast(list[Self | None], results)


AppConfigFragmentEdge = Edge[AppConfigFragmentGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for app config fragments.",
    ),
)
class AppConfigFragmentConnection(Connection[AppConfigFragmentGQL]):
    count: int = gql_field(
        description="Total number of app config fragments matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="The single scope a scoped fragment search runs at.",
    ),
    name="AppConfigFragmentScope",
)
class AppConfigFragmentScopeGQL(PydanticInputMixin[AppConfigFragmentScopeDTO]):
    scope_type: AppConfigScopeType = gql_field(
        description="Scope type: domain, user, or public (global)."
    )
    scope_id: UUID | None = gql_field(
        description=(
            "Scope identifier: the domain id (domain scope) or the user id (user scope). "
            "Null for public scope, which has no owner."
        ),
        default=None,
    )


# ---------------------------------------------------------------------------
# Filter / OrderBy
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter input for the fragment scope_type enum field.",
    ),
    name="AppConfigFragmentScopeTypeFilter",
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
        added_version=NEXT_RELEASE_VERSION,
        description="Filter input for querying app config fragments.",
    ),
    name="AppConfigFragmentFilter",
)
class AppConfigFragmentFilterGQL(PydanticInputMixin[AppConfigFragmentFilterDTO]):
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
    AND: list[Self] | None = gql_field(
        description="Match all of the given sub-filters.", default=None
    )
    OR: list[Self] | None = gql_field(
        description="Match any of the given sub-filters.", default=None
    )
    NOT: list[Self] | None = gql_field(description="Negate the given sub-filters.", default=None)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering app config fragment results.",
    ),
    name="AppConfigFragmentOrderField",
)
class AppConfigFragmentOrderFieldGQL(StrEnum):
    CONFIG_NAME = "config_name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Specifies ordering for app config fragment results.",
    ),
    name="AppConfigFragmentOrderBy",
)
class AppConfigFragmentOrderByGQL(PydanticInputMixin[AppConfigFragmentOrderDTO]):
    field: AppConfigFragmentOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)
