"""GraphQL types for the system session environ domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminResolveSystemSessionEnvironInput as AdminResolveSystemSessionEnvironInputDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    ResolveSystemSessionEnvironPayload as ResolveSystemSessionEnvironPayloadDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    SystemSessionEnvironNode as SystemSessionEnvironNodeDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScopeInfo as SystemSessionEnvironScopeInfoDTO,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

__all__ = (
    "AdminResolveSystemSessionEnvironInputGQL",
    "ResolveSystemSessionEnvironPayloadGQL",
    "SystemSessionEnvironNodeGQL",
    "SystemSessionEnvironScopeInfoGQL",
    "SystemSessionEnvironScopeTypeGQL",
    "SystemSessionEnvironValueSourceGQL",
)


SystemSessionEnvironValueSourceGQL = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Which value of a starting session a system session environ row injects.",
    ),
    SystemSessionEnvironValueSource,
    name="SystemSessionEnvironValueSource",
)


SystemSessionEnvironScopeTypeGQL = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Whether a system session environ row applies to every session, a domain's or a project's.",
    ),
    SystemSessionEnvironScopeType,
    name="SystemSessionEnvironScopeType",
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A system session environ row: the value it injects under its key at its scope.",
    ),
    model=SystemSessionEnvironNodeDTO,
    name="SystemSessionEnvironNode",
)
class SystemSessionEnvironNodeGQL(PydanticOutputMixin[SystemSessionEnvironNodeDTO]):
    entity_id: UUID = gql_field(description="The id of the row.")
    key: str = gql_field(
        description="The environment variable name the value is injected under."
    )
    value_source: SystemSessionEnvironValueSourceGQL = gql_field(
        description="Which value of the starting session is injected."
    )
    scope: SystemSessionEnvironScopeInfoGQL = gql_field(
        description="The scope the row is bound to."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="The rows a session in a domain and project receives, one per key.",
    ),
    model=ResolveSystemSessionEnvironPayloadDTO,
    name="ResolveSystemSessionEnvironPayload",
)
class ResolveSystemSessionEnvironPayloadGQL(
    PydanticOutputMixin[ResolveSystemSessionEnvironPayloadDTO]
):
    items: list[SystemSessionEnvironNodeGQL] = gql_field(
        description=(
            "Per key the enabled row at the most specific scope: project, domain, then public."
        )
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for reading the system session environ a session in a domain and project receives.",
    ),
    name="AdminResolveSystemSessionEnvironInput",
)
class AdminResolveSystemSessionEnvironInputGQL(
    PydanticInputMixin[AdminResolveSystemSessionEnvironInputDTO],
):
    domain_id: UUID = gql_field(description="The domain the session belongs to.")
    project_id: UUID = gql_field(description="The project the session belongs to.")
