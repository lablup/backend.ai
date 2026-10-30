"""GraphQL types for the system session environ domain."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self, cast, override
from uuid import UUID

from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    CreateSystemSessionEnvironInput as CreateSystemSessionEnvironInputDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    SystemSessionEnvironFilter as SystemSessionEnvironFilterDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    SystemSessionEnvironOrder as SystemSessionEnvironOrderDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    SystemSessionEnvironScopeTypeFilter as SystemSessionEnvironScopeTypeFilterDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    SystemSessionEnvironValueSourceFilter as SystemSessionEnvironValueSourceFilterDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    UpdateSystemSessionEnvironInput as UpdateSystemSessionEnvironInputDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    CreateSystemSessionEnvironPayload as CreateSystemSessionEnvironPayloadDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    DeleteSystemSessionEnvironPayload as DeleteSystemSessionEnvironPayloadDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    PurgeSystemSessionEnvironPayload as PurgeSystemSessionEnvironPayloadDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    RestoreSystemSessionEnvironPayload as RestoreSystemSessionEnvironPayloadDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    SystemSessionEnvironNode as SystemSessionEnvironNodeDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    UpdateSystemSessionEnvironPayload as UpdateSystemSessionEnvironPayloadDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironOrderField,
    SystemSessionEnvironScopeType,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScope as SystemSessionEnvironScopeDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScopeInfo as SystemSessionEnvironScopeInfoDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    NullableDateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
    UUIDScopeGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

__all__ = (
    "SystemSessionEnvironConnectionGQL",
    "SystemSessionEnvironEdgeGQL",
    "SystemSessionEnvironFilterGQL",
    "SystemSessionEnvironGQL",
    "SystemSessionEnvironOrderByGQL",
    "SystemSessionEnvironScopeGQL",
    "SystemSessionEnvironScopeInfoGQL",
    "CreateSystemSessionEnvironInputGQL",
    "CreateSystemSessionEnvironPayloadGQL",
    "UpdateSystemSessionEnvironInputGQL",
    "UpdateSystemSessionEnvironPayloadGQL",
    "DeleteSystemSessionEnvironPayloadGQL",
    "RestoreSystemSessionEnvironPayloadGQL",
    "PurgeSystemSessionEnvironPayloadGQL",
)


SystemSessionEnvironScopeTypeGQL = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Whether a system session environ row applies to every session, a domain's or a project's.",
    ),
    SystemSessionEnvironScopeType,
    name="SystemSessionEnvironScopeType",
)


SystemSessionEnvironOrderFieldGQL = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering system session environ rows.",
    ),
    SystemSessionEnvironOrderField,
    name="SystemSessionEnvironOrderField",
)


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="The scope a system session environ row is bound to.",
    ),
    model=SystemSessionEnvironScopeInfoDTO,
    name="SystemSessionEnvironScopeInfo",
)
class SystemSessionEnvironScopeInfoGQL(PydanticOutputMixin[SystemSessionEnvironScopeInfoDTO]):
    scope_type: SystemSessionEnvironScopeTypeGQL = gql_field(
        description="Whether the row applies to every session, a domain's or a project's."
    )
    scope_id: UUID = gql_field(
        description="The id of the public entity, the domain or the project the row is bound to."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A system session environ row: binds a value of a starting session to an "
            "environment variable name at the public scope, a domain or a project."
        ),
    ),
    name="SystemSessionEnviron",
)
class SystemSessionEnvironGQL(PydanticNodeMixin[SystemSessionEnvironNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    entity_id: UUID = gql_field(description="The id of the row.")
    key: str = gql_field(description="The environment variable name the value is injected under.")
    value_source: str = gql_field(
        description=(
            "Which value of the starting session is injected, as a value source name "
            "systemSessionEnvironValueSources lists."
        )
    )
    scope: SystemSessionEnvironScopeInfoGQL = gql_field(
        description="The scope the row is bound to."
    )
    created_at: datetime = gql_field(description="When the row was created.")
    updated_at: datetime = gql_field(description="When the row was last changed.")
    deleted_at: datetime | None = gql_field(
        description="When the row was soft-deleted, or null if it is not."
    )

    @classmethod
    @override
    async def resolve_nodes(
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self]:
        results = await info.context.data_loaders.system_session_environ_loader.load_many([
            SystemSessionEnvironID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self], results)


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One system session environ row within a connection.",
    ),
    name="SystemSessionEnvironEdge",
)
class SystemSessionEnvironEdgeGQL(Edge[SystemSessionEnvironGQL]):
    pass


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for system session environ rows.",
    ),
    name="SystemSessionEnvironConnection",
)
class SystemSessionEnvironConnectionGQL(Connection[SystemSessionEnvironGQL]):
    edges: list[SystemSessionEnvironEdgeGQL] = gql_field(  # type: ignore[assignment]
        description="Contains the nodes in this connection."
    )
    count: int = gql_field(description="Total number of rows matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Filter by value source name with equality and membership operators. The names are "
            "the ones systemSessionEnvironValueSources lists."
        ),
    ),
    name="SystemSessionEnvironValueSourceFilter",
)
class SystemSessionEnvironValueSourceFilterGQL(
    PydanticInputMixin[SystemSessionEnvironValueSourceFilterDTO]
):
    equals: str | None = gql_field(description="Exact match.", default=None)
    in_: list[str] | None = gql_field(
        description="Match any of the provided values.", name="in", default=None
    )
    not_equals: str | None = gql_field(description="Exclude an exact match.", default=None)
    not_in: list[str] | None = gql_field(
        description="Exclude any of the provided values.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the scope type with equality and membership operators.",
    ),
    name="SystemSessionEnvironScopeTypeFilter",
)
class SystemSessionEnvironScopeTypeFilterGQL(
    PydanticInputMixin[SystemSessionEnvironScopeTypeFilterDTO]
):
    equals: SystemSessionEnvironScopeTypeGQL | None = gql_field(
        description="Exact match.", default=None
    )
    in_: list[SystemSessionEnvironScopeTypeGQL] | None = gql_field(
        description="Match any of the provided values.", name="in", default=None
    )
    not_equals: SystemSessionEnvironScopeTypeGQL | None = gql_field(
        description="Exclude an exact match.", default=None
    )
    not_in: list[SystemSessionEnvironScopeTypeGQL] | None = gql_field(
        description="Exclude any of the provided values.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for system session environ rows.",
    ),
    name="SystemSessionEnvironFilter",
)
class SystemSessionEnvironFilterGQL(PydanticInputMixin[SystemSessionEnvironFilterDTO]):
    entity_id: UUIDFilter | None = gql_field(description="Filter by the row's id.", default=None)
    key: StringFilter | None = gql_field(
        description="Filter by the environment variable name.", default=None
    )
    value_source: SystemSessionEnvironValueSourceFilterGQL | None = gql_field(
        description="Filter by which value of the starting session is injected.", default=None
    )
    scope_type: SystemSessionEnvironScopeTypeFilterGQL | None = gql_field(
        description="Filter by the kind of scope the row is bound to.", default=None
    )
    scope_id: UUIDFilter | None = gql_field(
        description="Filter by the id of the public entity, the domain or the project.",
        default=None,
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by when the row was created.", default=None
    )
    updated_at: DateTimeFilter | None = gql_field(
        description="Filter by when the row was last changed.", default=None
    )
    deleted_at: NullableDateTimeFilter | None = gql_field(
        description="Filter by when the row was soft-deleted.", default=None
    )
    AND: list[Self] | None = gql_field(
        description="Combine multiple filters with AND logic.", default=None
    )
    OR: list[Self] | None = gql_field(
        description="Combine multiple filters with OR logic.", default=None
    )
    NOT: list[Self] | None = gql_field(description="Negate the given filters.", default=None)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One ordering rule for a system session environ search.",
    ),
    name="SystemSessionEnvironOrderBy",
)
class SystemSessionEnvironOrderByGQL(PydanticInputMixin[SystemSessionEnvironOrderDTO]):
    field: SystemSessionEnvironOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scope for the scoped system session environ query. Each list is OR'd internally "
            "and across lists, and every scope named is authorized before the read runs."
        ),
    ),
    name="SystemSessionEnvironScope",
)
class SystemSessionEnvironScopeGQL(PydanticInputMixin[SystemSessionEnvironScopeDTO]):
    domain: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Domains whose rows are being read."
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects whose rows are being read."
    )
    public: bool = gql_field(default=False, description="Include the rows registered in public.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for binding a value source to an environment variable name at one scope."
        ),
    ),
    name="CreateSystemSessionEnvironInput",
)
class CreateSystemSessionEnvironInputGQL(PydanticInputMixin[CreateSystemSessionEnvironInputDTO]):
    key: str = gql_field(description="The environment variable name the value is injected under.")
    value_source: str = gql_field(
        description=(
            "Which value of the starting session is injected, as a value source name "
            "systemSessionEnvironValueSources lists."
        )
    )
    scope_type: SystemSessionEnvironScopeTypeGQL = gql_field(
        description="Whether the row applies to every session, a domain's or a project's."
    )
    scope_id: UUID | None = gql_field(
        default=None, description="The id of the domain or the project. Left out for public."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a system session environ row create.",
    ),
    model=CreateSystemSessionEnvironPayloadDTO,
    name="CreateSystemSessionEnvironPayload",
)
class CreateSystemSessionEnvironPayloadGQL(
    PydanticOutputMixin[CreateSystemSessionEnvironPayloadDTO]
):
    system_session_environ: SystemSessionEnvironGQL = gql_field(description="The created row.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for changing a system session environ row's key.",
    ),
    name="UpdateSystemSessionEnvironInput",
)
class UpdateSystemSessionEnvironInputGQL(PydanticInputMixin[UpdateSystemSessionEnvironInputDTO]):
    key: str | None = gql_field(default=UNSET, description="New environment variable name.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a system session environ row update.",
    ),
    model=UpdateSystemSessionEnvironPayloadDTO,
    name="UpdateSystemSessionEnvironPayload",
)
class UpdateSystemSessionEnvironPayloadGQL(
    PydanticOutputMixin[UpdateSystemSessionEnvironPayloadDTO]
):
    system_session_environ: SystemSessionEnvironGQL = gql_field(description="The updated row.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a system session environ row soft delete.",
    ),
    model=DeleteSystemSessionEnvironPayloadDTO,
    name="DeleteSystemSessionEnvironPayload",
)
class DeleteSystemSessionEnvironPayloadGQL(
    PydanticOutputMixin[DeleteSystemSessionEnvironPayloadDTO]
):
    system_session_environ: SystemSessionEnvironGQL = gql_field(description="The soft-deleted row.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a system session environ row restore.",
    ),
    model=RestoreSystemSessionEnvironPayloadDTO,
    name="RestoreSystemSessionEnvironPayload",
)
class RestoreSystemSessionEnvironPayloadGQL(
    PydanticOutputMixin[RestoreSystemSessionEnvironPayloadDTO]
):
    system_session_environ: SystemSessionEnvironGQL = gql_field(description="The restored row.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a system session environ row purge.",
    ),
    model=PurgeSystemSessionEnvironPayloadDTO,
    name="PurgeSystemSessionEnvironPayload",
)
class PurgeSystemSessionEnvironPayloadGQL(PydanticOutputMixin[PurgeSystemSessionEnvironPayloadDTO]):
    purged_id: ID = gql_field(description="Global ID of the purged row.")
    entity_id: UUID = gql_field(description="The id of the purged row.")
