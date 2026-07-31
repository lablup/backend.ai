from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, override
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    CreateIdleCheckerAssignmentInput as CreateIdleCheckerAssignmentInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentFilter as IdleCheckerAssignmentFilterDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentOrder as IdleCheckerAssignmentOrderDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentScopeDTO,
    IdleCheckerScopeRefDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    PurgeIdleCheckerAssignmentInput as PurgeIdleCheckerAssignmentInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    UpdateIdleCheckerAssignmentInput as UpdateIdleCheckerAssignmentInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    CreateIdleCheckerAssignmentPayload as CreateIdleCheckerAssignmentPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    IdleCheckerAssignmentNode,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    PurgeIdleCheckerAssignmentPayload as PurgeIdleCheckerAssignmentPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    UpdateIdleCheckerAssignmentPayload as UpdateIdleCheckerAssignmentPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import (
    ScopeTypeFilter as ScopeTypeFilterDTO,
)
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    UUIDFilter,
)
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
from ai.backend.manager.errors.api import NotImplementedAPI

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.idle_checker.types import IdleCheckerGQL


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Identifies the kind of scope an idle checker assignment applies to. "
            "The value determines how the scope identifier is interpreted."
        ),
    ),
    name="IdleCheckerScopeType",
)
class IdleCheckerScopeTypeGQL(StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    RESOURCE_GROUP = "resource_group"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "References a single scope as a typed (scopeType, scopeId) pair. "
            "The identifier is interpreted according to the scope type."
        ),
    ),
    name="IdleCheckerScopeRef",
)
class IdleCheckerScopeRefGQL(PydanticInputMixin[IdleCheckerScopeRefDTO]):
    scope_type: IdleCheckerScopeTypeGQL = gql_field(description="Kind of the scope.")
    scope_id: UUID = gql_field(
        description="Scope identifier, interpreted according to the scope type."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Scope for the scoped idle checker assignment query. "
            "All items are OR'd; the item list must not be empty."
        ),
    ),
    name="IdleCheckerAssignmentScope",
)
class IdleCheckerAssignmentScopeGQL(PydanticInputMixin[IdleCheckerAssignmentScopeDTO]):
    items: list[IdleCheckerScopeRefGQL] = gql_field(
        description="Scope-tagged items (OR across all items)."
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Represents one association between a scope and a reusable idle checker. "
            "The scope and checker are the assignment's immutable identity; "
            "the enabled flag controls whether the association participates."
        ),
    ),
    name="IdleCheckerAssignment",
)
class IdleCheckerAssignmentGQL(PydanticNodeMixin[IdleCheckerAssignmentNode]):
    id: NodeID[str] = gql_field(
        description="Relay global node identifier backed by the assignment's UUID."
    )
    scope_type: IdleCheckerScopeTypeGQL = gql_field(description="Kind of the bound scope.")
    scope_id: UUID = gql_field(
        description="Scope identifier, interpreted according to the scope type."
    )
    idle_checker_id: UUID = gql_field(description="ID of the bound idle checker.")
    enabled: bool = gql_field(description="Whether the assignment participates in idle checking.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")

    @gql_field(description="The bound idle checker definition.")  # type: ignore[misc]
    async def idle_checker(
        self,
        info: Info,
    ) -> Annotated[
        IdleCheckerGQL,
        strawberry.lazy("ai.backend.manager.api.gql.idle_checker.types"),
    ]:
        raise NotImplementedAPI("Idle checker resolution on assignments is not implemented.")

    @classmethod
    @override
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Self]:
        raise NotImplementedAPI("Idle checker assignment node resolution is not implemented.")


IdleCheckerAssignmentEdgeGQL = Edge[IdleCheckerAssignmentGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Provides a paginated collection of idle checker assignments. "
            "The count reports all records matching the supplied filter."
        ),
    ),
    name="IdleCheckerAssignmentConnection",
)
class IdleCheckerAssignmentConnectionGQL(Connection[IdleCheckerAssignmentGQL]):
    count: int = gql_field(description="Total number of matching idle checker assignments.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Filters idle checker assignments by their scope type. "
            "Use either an exact value or a list of accepted values."
        ),
    ),
    name="IdleCheckerScopeTypeFilter",
)
class IdleCheckerScopeTypeFilterGQL(PydanticInputMixin[ScopeTypeFilterDTO]):
    equals: IdleCheckerScopeTypeGQL | None = gql_field(
        description="Exact scope type.", default=None
    )
    in_: list[IdleCheckerScopeTypeGQL] | None = gql_field(
        description="Allowed scope types.",
        name="in",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Defines criteria for searching idle checker assignments. "
            "Nested logical fields can combine or negate multiple criteria."
        ),
    ),
    name="IdleCheckerAssignmentFilter",
)
class IdleCheckerAssignmentFilterGQL(PydanticInputMixin[IdleCheckerAssignmentFilterDTO]):
    scope_type: IdleCheckerScopeTypeFilterGQL | None = gql_field(
        description="Scope type filter.",
        default=None,
    )
    scope_id: UUIDFilter | None = gql_field(description="Scope identifier filter.", default=None)
    idle_checker_id: UUIDFilter | None = gql_field(
        description="Bound idle checker ID filter.",
        default=None,
    )
    enabled: bool | None = gql_field(description="Filter by the enabled flag.", default=None)
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
        added_version="26.8.0",
        description=(
            "Lists fields that can determine idle checker assignment result order. "
            "Each field is paired with an ascending or descending direction."
        ),
    ),
    name="IdleCheckerAssignmentOrderField",
)
class IdleCheckerAssignmentOrderFieldGQL(StrEnum):
    SCOPE_TYPE = "scope_type"
    ENABLED = "enabled"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Defines one ordering rule for an idle checker assignment search. "
            "Multiple rules are applied in the order they are supplied."
        ),
    ),
    name="IdleCheckerAssignmentOrderBy",
)
class IdleCheckerAssignmentOrderByGQL(PydanticInputMixin[IdleCheckerAssignmentOrderDTO]):
    field: IdleCheckerAssignmentOrderFieldGQL = gql_field(description="Order field.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Binds a global idle checker to a single scope. "
            "Requires permission on the given scope (subject to RBAC)."
        ),
    ),
    name="CreateIdleCheckerAssignmentInput",
)
class CreateIdleCheckerAssignmentInputGQL(PydanticInputMixin[CreateIdleCheckerAssignmentInputDTO]):
    scope: IdleCheckerScopeRefGQL = gql_field(description="Scope the checker is bound to.")
    idle_checker_id: UUID = gql_field(description="Idle checker to bind.")
    enabled: bool = gql_field(
        description="Whether the assignment participates in idle checking.",
        default=True,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Updates an idle checker assignment's enabled state. "
            "The bound scope and checker are immutable; rebind by purging and recreating."
        ),
    ),
    name="UpdateIdleCheckerAssignmentInput",
)
class UpdateIdleCheckerAssignmentInputGQL(PydanticInputMixin[UpdateIdleCheckerAssignmentInputDTO]):
    id: UUID = gql_field(description="Idle checker assignment ID to update.")
    enabled: bool = gql_field(description="New enabled state.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description="Identifies the idle checker assignment to purge.",
    ),
    name="PurgeIdleCheckerAssignmentInput",
)
class PurgeIdleCheckerAssignmentInputGQL(PydanticInputMixin[PurgeIdleCheckerAssignmentInputDTO]):
    id: UUID = gql_field(description="Idle checker assignment ID to purge.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Returns the created idle checker assignment. The node contains the "
            "server-assigned identifier and timestamps."
        ),
    ),
    model=CreateIdleCheckerAssignmentPayloadDTO,
    name="CreateIdleCheckerAssignmentPayload",
)
class CreateIdleCheckerAssignmentPayloadGQL(
    PydanticOutputMixin[CreateIdleCheckerAssignmentPayloadDTO]
):
    idle_checker_assignment: IdleCheckerAssignmentGQL = gql_field(
        description="Created idle checker assignment."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Returns the idle checker assignment after an update is applied. "
            "The node reflects the complete persisted state, including unchanged fields."
        ),
    ),
    model=UpdateIdleCheckerAssignmentPayloadDTO,
    name="UpdateIdleCheckerAssignmentPayload",
)
class UpdateIdleCheckerAssignmentPayloadGQL(
    PydanticOutputMixin[UpdateIdleCheckerAssignmentPayloadDTO]
):
    idle_checker_assignment: IdleCheckerAssignmentGQL = gql_field(
        description="Updated idle checker assignment."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Confirms that an idle checker assignment was permanently removed. "
            "The returned identifier refers to the deleted assignment."
        ),
    ),
    model=PurgeIdleCheckerAssignmentPayloadDTO,
    name="PurgeIdleCheckerAssignmentPayload",
)
class PurgeIdleCheckerAssignmentPayloadGQL(
    PydanticOutputMixin[PurgeIdleCheckerAssignmentPayloadDTO]
):
    id: UUID = gql_field(description="Purged idle checker assignment ID.")
