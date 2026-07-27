from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, override
from uuid import UUID

from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput as CreateIdleCheckerInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    IdleCheckerFilter as IdleCheckerFilterDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    IdleCheckerOrder as IdleCheckerOrderDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    IdleCheckerScope as IdleCheckerScopeDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    IdleCheckerSpecInputDTO,
    SessionLifetimeSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    UpdateIdleCheckerInput as UpdateIdleCheckerInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    CreateIdleCheckerPayload as CreateIdleCheckerPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    IdleCheckerNode,
    IdleCheckerSpecInfo,
    SessionLifetimeSpecInfo,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    PurgeIdleCheckerPayload as PurgeIdleCheckerPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    UpdateIdleCheckerPayload as UpdateIdleCheckerPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import (
    CheckerTypeFilter as CheckerTypeFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import SessionTypes
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
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.errors.api import NotImplementedAPI


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Identifies the implementation used to evaluate an idle condition. "
            "The value determines how the checker specification is interpreted."
        ),
    ),
    name="IdleCheckerType",
)
class IdleCheckerTypeGQL(StrEnum):
    SESSION_LIFETIME = "session_lifetime"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Lists checker implementations accepted by create and update operations. "
            "Only implementations fully supported by this API version are exposed."
        ),
    ),
    name="IdleCheckerInputType",
)
class IdleCheckerInputTypeGQL(StrEnum):
    SESSION_LIFETIME = "session_lifetime"


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Identifies the kind of scope to which an idle checker is bound.",
    ),
    name="IdleCheckerScopeType",
)
class IdleCheckerScopeTypeGQL(StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    RESOURCE_GROUP = "resource_group"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Identifies a scope where an idle checker is managed and applied.",
    ),
    name="IdleCheckerScope",
)
class IdleCheckerScopeGQL(PydanticInputMixin[IdleCheckerScopeDTO]):
    scope_type: IdleCheckerScopeTypeGQL = gql_field(
        description="Binding scope type.",
    )
    scope_id: UUID = gql_field(
        description="UUID of the scope.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Configures the maximum lifetime of a running session. "
            "The checker expires a session after the configured duration is reached."
        ),
    ),
    model=SessionLifetimeSpecInfo,
    name="SessionLifetimeIdleCheckerSpec",
)
class SessionLifetimeIdleCheckerSpecGQL:
    max_lifetime_seconds: int = gql_field(description="Maximum session lifetime in seconds.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Contains the settings used by an idle checker implementation. "
            "This API version exposes session-lifetime settings only."
        ),
    ),
    model=IdleCheckerSpecInfo,
    name="IdleCheckerSpec",
)
class IdleCheckerSpecGQL:
    type: IdleCheckerTypeGQL = gql_field(description="Checker implementation type.")
    session_lifetime: SessionLifetimeIdleCheckerSpecGQL = gql_field(
        description="Settings that define the maximum lifetime of a session.",
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Represents a reusable idle checker definition independent of its bindings. "
            "It includes target session types, a grace period, and typed checker settings."
        ),
    ),
    name="IdleChecker",
)
class IdleCheckerGQL(PydanticNodeMixin[IdleCheckerNode]):
    id: NodeID[str] = gql_field(
        description="Relay global node identifier backed by the idle checker's UUID."
    )
    name: str = gql_field(description="Idle checker name.")
    description: str | None = gql_field(description="Optional description.")
    checker_type: IdleCheckerTypeGQL = gql_field(description="Checker implementation type.")
    target_session_types: list[SessionTypes] = gql_field(
        description="Session types evaluated by this checker."
    )
    initial_grace_period_seconds: int = gql_field(description="Initial grace period in seconds.")
    spec: IdleCheckerSpecGQL = gql_field(description="Typed idle checker specification.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")

    @classmethod
    @override
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Self]:
        raise NotImplementedAPI("Idle checker node resolution is not implemented.")


IdleCheckerEdgeGQL = Edge[IdleCheckerGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Provides a paginated collection of idle checker definitions available in a scope. "
            "The count reports all records matching the supplied filter."
        ),
    ),
    name="IdleCheckerConnection",
)
class IdleCheckerConnectionGQL(Connection[IdleCheckerGQL]):
    count: int = gql_field(description="Total number of matching idle checkers.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Supplies settings for a session-lifetime checker. "
            "The lifetime is measured in seconds from the session's effective start."
        ),
    ),
    name="SessionLifetimeIdleCheckerSpecInput",
)
class SessionLifetimeIdleCheckerSpecInputGQL(PydanticInputMixin[SessionLifetimeSpecInputDTO]):
    max_lifetime_seconds: int = gql_field(description="Maximum session lifetime in seconds.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Supplies the implementation-specific settings for an idle checker. "
            "This API version accepts session-lifetime settings only."
        ),
    ),
    name="IdleCheckerSpecInput",
)
class IdleCheckerSpecInputGQL(PydanticInputMixin[IdleCheckerSpecInputDTO]):
    type: IdleCheckerInputTypeGQL = gql_field(description="Checker implementation type.")
    session_lifetime: SessionLifetimeIdleCheckerSpecInputGQL = gql_field(
        description="Session-lifetime checker settings.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Filters idle checkers by their implementation type. "
            "Use either an exact value or a list of accepted values."
        ),
    ),
    name="IdleCheckerTypeFilter",
)
class IdleCheckerTypeFilterGQL(PydanticInputMixin[CheckerTypeFilterDTO]):
    equals: IdleCheckerTypeGQL | None = gql_field(description="Exact checker type.", default=None)
    in_: list[IdleCheckerTypeGQL] | None = gql_field(
        description="Allowed checker types.",
        name="in",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Defines criteria for searching registered idle checkers. "
            "Nested logical fields can combine or negate multiple criteria."
        ),
    ),
    name="IdleCheckerFilter",
)
class IdleCheckerFilterGQL(PydanticInputMixin[IdleCheckerFilterDTO]):
    name: StringFilter | None = gql_field(description="Name filter.", default=None)
    checker_type: IdleCheckerTypeFilterGQL | None = gql_field(
        description="Checker type filter.",
        default=None,
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Creation timestamp filter.",
        default=None,
    )
    updated_at: DateTimeFilter | None = gql_field(
        description="Update timestamp filter.",
        default=None,
    )
    AND: list[Self] | None = gql_field(description="Match all nested filters.", default=None)
    OR: list[Self] | None = gql_field(description="Match any nested filter.", default=None)
    NOT: list[Self] | None = gql_field(description="Negate nested filters.", default=None)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Lists fields that can determine idle checker result order. "
            "Each field is paired with an ascending or descending direction."
        ),
    ),
    name="IdleCheckerOrderField",
)
class IdleCheckerOrderFieldGQL(StrEnum):
    NAME = "name"
    CHECKER_TYPE = "checker_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Defines one ordering rule for an idle checker search. "
            "Multiple rules are applied in the order they are supplied."
        ),
    ),
    name="IdleCheckerOrderBy",
)
class IdleCheckerOrderByGQL(PydanticInputMixin[IdleCheckerOrderDTO]):
    field: IdleCheckerOrderFieldGQL = gql_field(description="Order field.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Defines a reusable idle checker specification. "
            "The create mutation separately receives the scope where it is managed and applied."
        ),
    ),
    name="CreateIdleCheckerInput",
)
class CreateIdleCheckerInputGQL(PydanticInputMixin[CreateIdleCheckerInputDTO]):
    name: str = gql_field(description="Idle checker name.")
    description: str = gql_field(description="Idle checker description.")
    checker_type: IdleCheckerInputTypeGQL = gql_field(description="Checker implementation type.")
    target_session_types: list[SessionTypes] = gql_field(description="Target session types.")
    initial_grace_period_seconds: int = gql_field(
        description="Initial grace period in seconds.",
        default=0,
    )
    checker_spec: IdleCheckerSpecInputGQL = gql_field(description="Typed checker specification.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Applies a partial update to an existing idle checker. "
            "Only fields supplied with non-null values are replaced."
        ),
    ),
    name="UpdateIdleCheckerInput",
)
class UpdateIdleCheckerInputGQL(PydanticInputMixin[UpdateIdleCheckerInputDTO]):
    name: str | None = gql_field(description="New name.", default=UNSET)
    description: str | None = gql_field(
        description="New description; omit it or pass null to keep the current value.",
        default=UNSET,
    )
    target_session_types: list[SessionTypes] | None = gql_field(
        description="New target session types.",
        default=UNSET,
    )
    initial_grace_period_seconds: int | None = gql_field(
        description="New initial grace period.",
        default=UNSET,
    )
    checker_spec: IdleCheckerSpecInputGQL | None = gql_field(
        description="New checker specification.",
        default=UNSET,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Returns the idle checker created and bound to the requested scope. "
            "The node contains the server-assigned identifier and timestamps."
        ),
    ),
    model=CreateIdleCheckerPayloadDTO,
    name="CreateIdleCheckerPayload",
)
class CreateIdleCheckerPayloadGQL:
    idle_checker: IdleCheckerGQL = gql_field(description="Created idle checker.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Returns the idle checker after an update is applied. "
            "The node reflects the complete persisted state, including unchanged fields."
        ),
    ),
    model=UpdateIdleCheckerPayloadDTO,
    name="UpdateIdleCheckerPayload",
)
class UpdateIdleCheckerPayloadGQL:
    idle_checker: IdleCheckerGQL = gql_field(description="Updated idle checker.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Confirms that an idle checker was permanently removed. "
            "The returned identifier refers to the deleted checker."
        ),
    ),
    model=PurgeIdleCheckerPayloadDTO,
    name="PurgeIdleCheckerPayload",
)
class PurgeIdleCheckerPayloadGQL:
    id: UUID = gql_field(description="Purged idle checker ID.")
