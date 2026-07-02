"""GraphQL types for app config definition."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, cast, override
from uuid import UUID

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionFilter as AppConfigDefinitionFilterDTO,
)
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionOrder as AppConfigDefinitionOrderDTO,
)
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput as CreateAppConfigDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    PurgeAppConfigDefinitionInput as PurgeAppConfigDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    CreateAppConfigDefinitionPayload as CreateAppConfigDefinitionPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    PurgeAppConfigDefinitionPayload as PurgeAppConfigDefinitionPayloadDTO,
)
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "AppConfigDefinitionConnection",
    "AppConfigDefinitionEdge",
    "AppConfigDefinitionFilterGQL",
    "AppConfigDefinitionGQL",
    "AppConfigDefinitionOrderByGQL",
    "AppConfigDefinitionOrderFieldGQL",
    "CreateAppConfigDefinitionInputGQL",
    "CreateAppConfigDefinitionPayloadGQL",
    "PurgeAppConfigDefinitionInputGQL",
    "PurgeAppConfigDefinitionPayloadGQL",
)


# ---------------------------------------------------------------------------
# Node / Edge / Connection
# ---------------------------------------------------------------------------


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A registered app config.",
    ),
    name="AppConfigDefinition",
)
class AppConfigDefinitionGQL(PydanticNodeMixin[AppConfigDefinitionNode]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node identifier for the app config definition."
    )
    config_name: str = gql_field(description="Registered config name.")
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
        results = await info.context.data_loaders.app_config_definition_loader.load_many([
            AppConfigDefinitionID(UUID(nid)) for nid in node_ids
        ])
        return cast(list[Self | None], results)


AppConfigDefinitionEdge = Edge[AppConfigDefinitionGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for app config definition records.",
    ),
)
class AppConfigDefinitionConnection(Connection[AppConfigDefinitionGQL]):
    count: int = gql_field(
        description="Total number of app config definition records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# ---------------------------------------------------------------------------
# Filter / OrderBy
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying app config definitions.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AppConfigDefinitionFilter",
)
class AppConfigDefinitionFilterGQL(PydanticInputMixin[AppConfigDefinitionFilterDTO]):
    config_name: StringFilter | None = gql_field(description="Filter by config name.", default=None)
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation datetime.", default=None
    )
    updated_at: DateTimeFilter | None = gql_field(
        description="Filter by last update datetime.", default=None
    )
    AND: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="Match all of the given sub-filters."
        ),
        default=None,
    )
    OR: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="Match any of the given sub-filters."
        ),
        default=None,
    )
    NOT: list[Self] | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="Negate the given sub-filters."
        ),
        default=None,
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering app config definition results.",
    ),
    name="AppConfigDefinitionOrderField",
)
class AppConfigDefinitionOrderFieldGQL(StrEnum):
    CONFIG_NAME = "config_name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for app config definition results.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AppConfigDefinitionOrderBy",
)
class AppConfigDefinitionOrderByGQL(PydanticInputMixin[AppConfigDefinitionOrderDTO]):
    field: AppConfigDefinitionOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)


# ---------------------------------------------------------------------------
# Mutation inputs / payloads
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for registering a new app config definition.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="CreateAppConfigDefinitionInput",
)
class CreateAppConfigDefinitionInputGQL(PydanticInputMixin[CreateAppConfigDefinitionInputDTO]):
    config_name: str = gql_field(description="Unique config name to register.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for purging an app config definition.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="PurgeAppConfigDefinitionInput",
)
class PurgeAppConfigDefinitionInputGQL(PydanticInputMixin[PurgeAppConfigDefinitionInputDTO]):
    id: UUID = gql_field(description="App config definition id to purge.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for app config definition creation.",
    ),
    model=CreateAppConfigDefinitionPayloadDTO,
    name="CreateAppConfigDefinitionPayload",
)
class CreateAppConfigDefinitionPayloadGQL(PydanticOutputMixin[CreateAppConfigDefinitionPayloadDTO]):
    app_config_definition: AppConfigDefinitionGQL = gql_field(
        description="The created app config definition."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for app config definition purge.",
    ),
    model=PurgeAppConfigDefinitionPayloadDTO,
    all_fields=True,
    name="PurgeAppConfigDefinitionPayload",
)
class PurgeAppConfigDefinitionPayloadGQL(PydanticOutputMixin[PurgeAppConfigDefinitionPayloadDTO]):
    pass
