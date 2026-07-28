from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, override
from uuid import UUID

import strawberry
from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    CreateIdleCheckerBindingInput as CreateIdleCheckerBindingInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    IdleCheckerBindingFilter as IdleCheckerBindingFilterDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    IdleCheckerBindingOptionsInputDTO,
    IdleCheckerBindingScopeDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    IdleCheckerBindingOrder as IdleCheckerBindingOrderDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    PurgeIdleCheckerBindingInput as PurgeIdleCheckerBindingInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    UpdateIdleCheckerBindingInput as UpdateIdleCheckerBindingInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.response import (
    CreateIdleCheckerBindingPayload as CreateIdleCheckerBindingPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.response import (
    IdleCheckerBindingNode,
    IdleCheckerBindingOptionsInfo,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.response import (
    PurgeIdleCheckerBindingPayload as PurgeIdleCheckerBindingPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.response import (
    UpdateIdleCheckerBindingPayload as UpdateIdleCheckerBindingPayloadDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.types import (
    ScopeTypeFilter as ScopeTypeFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.errors.api import NotImplementedAPI

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.idle_checker.types import IdleCheckerGQL


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Identifies the kind of scope an idle checker binding applies to. "
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
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Identifies a single scope an idle checker binding applies to. "
            "Exactly one scope field must be provided."
        ),
    ),
    name="IdleCheckerBindingScope",
    one_of=True,
)
class IdleCheckerBindingScopeGQL(PydanticInputMixin[IdleCheckerBindingScopeDTO]):
    domain: UUID | None = gql_field(description="Domain ID.", default=UNSET)
    project: UUID | None = gql_field(description="Project ID.", default=UNSET)
    resource_group: UUID | None = gql_field(description="Resource group ID.", default=UNSET)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Supplies binding-level options. "
            "Omitted fields use their defaults on create or keep the current value on update."
        ),
    ),
    name="IdleCheckerBindingOptionsInput",
)
class IdleCheckerBindingOptionsInputGQL(PydanticInputMixin[IdleCheckerBindingOptionsInputDTO]):
    enabled: bool | None = gql_field(
        description=(
            "Whether the binding participates in idle checking. "
            "Omit to use the default (true) on create or to keep the current value on update."
        ),
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Contains the binding-level options of an idle checker binding.",
    ),
    model=IdleCheckerBindingOptionsInfo,
    name="IdleCheckerBindingOptions",
)
class IdleCheckerBindingOptionsGQL:
    enabled: bool = gql_field(
        description="Whether the binding participates in idle checking.",
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Represents one association between a scope and a reusable idle checker. "
            "The scope and checker are the binding's immutable identity; "
            "binding-level options control how the association participates."
        ),
    ),
    name="IdleCheckerBinding",
)
class IdleCheckerBindingGQL(PydanticNodeMixin[IdleCheckerBindingNode]):
    id: NodeID[str] = gql_field(
        description="Relay global node identifier backed by the binding's UUID."
    )
    scope_type: IdleCheckerScopeTypeGQL = gql_field(description="Kind of the bound scope.")
    scope_id: UUID = gql_field(
        description="Scope identifier: the domain, project, or resource group ID."
    )
    idle_checker_id: UUID = gql_field(description="ID of the bound idle checker.")
    options: IdleCheckerBindingOptionsGQL = gql_field(description="Binding-level options.")
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
        raise NotImplementedAPI("Idle checker resolution on bindings is not implemented.")

    @classmethod
    @override
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Self]:
        raise NotImplementedAPI("Idle checker binding node resolution is not implemented.")


IdleCheckerBindingEdgeGQL = Edge[IdleCheckerBindingGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Provides a paginated collection of idle checker bindings. "
            "The count reports all records matching the supplied filter."
        ),
    ),
    name="IdleCheckerBindingConnection",
)
class IdleCheckerBindingConnectionGQL(Connection[IdleCheckerBindingGQL]):
    count: int = gql_field(description="Total number of matching idle checker bindings.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Filters idle checker bindings by their scope type. "
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
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Defines criteria for searching idle checker bindings. "
            "Nested logical fields can combine or negate multiple criteria."
        ),
    ),
    name="IdleCheckerBindingFilter",
)
class IdleCheckerBindingFilterGQL(PydanticInputMixin[IdleCheckerBindingFilterDTO]):
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
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Lists fields that can determine idle checker binding result order. "
            "Each field is paired with an ascending or descending direction."
        ),
    ),
    name="IdleCheckerBindingOrderField",
)
class IdleCheckerBindingOrderFieldGQL(StrEnum):
    SCOPE_TYPE = "scope_type"
    ENABLED = "enabled"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Defines one ordering rule for an idle checker binding search. "
            "Multiple rules are applied in the order they are supplied."
        ),
    ),
    name="IdleCheckerBindingOrderBy",
)
class IdleCheckerBindingOrderByGQL(PydanticInputMixin[IdleCheckerBindingOrderDTO]):
    field: IdleCheckerBindingOrderFieldGQL = gql_field(description="Order field.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Binds a global idle checker to a single scope. "
            "Requires permission on the given scope (subject to RBAC)."
        ),
    ),
    name="CreateIdleCheckerBindingInput",
)
class CreateIdleCheckerBindingInputGQL(PydanticInputMixin[CreateIdleCheckerBindingInputDTO]):
    scope: IdleCheckerBindingScopeGQL = gql_field(description="Scope the checker is bound to.")
    idle_checker_id: UUID = gql_field(description="Idle checker to bind.")
    options: IdleCheckerBindingOptionsInputGQL | None = gql_field(
        description="Binding options; omit to use the defaults.",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Replaces an idle checker binding's options. "
            "The bound scope and checker are immutable; rebind by purging and recreating."
        ),
    ),
    name="UpdateIdleCheckerBindingInput",
)
class UpdateIdleCheckerBindingInputGQL(PydanticInputMixin[UpdateIdleCheckerBindingInputDTO]):
    id: UUID = gql_field(description="Idle checker binding ID to update.")
    options: IdleCheckerBindingOptionsInputGQL = gql_field(description="New binding options.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Identifies the idle checker binding to purge.",
    ),
    name="PurgeIdleCheckerBindingInput",
)
class PurgeIdleCheckerBindingInputGQL(PydanticInputMixin[PurgeIdleCheckerBindingInputDTO]):
    id: UUID = gql_field(description="Idle checker binding ID to purge.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Returns the created idle checker binding. The node contains the "
            "server-assigned identifier and timestamps."
        ),
    ),
    model=CreateIdleCheckerBindingPayloadDTO,
    name="CreateIdleCheckerBindingPayload",
)
class CreateIdleCheckerBindingPayloadGQL:
    idle_checker_binding: IdleCheckerBindingGQL = gql_field(
        description="Created idle checker binding."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Returns the idle checker binding after an update is applied. "
            "The node reflects the complete persisted state, including unchanged fields."
        ),
    ),
    model=UpdateIdleCheckerBindingPayloadDTO,
    name="UpdateIdleCheckerBindingPayload",
)
class UpdateIdleCheckerBindingPayloadGQL:
    idle_checker_binding: IdleCheckerBindingGQL = gql_field(
        description="Updated idle checker binding."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Confirms that an idle checker binding was permanently removed. "
            "The returned identifier refers to the deleted binding."
        ),
    ),
    model=PurgeIdleCheckerBindingPayloadDTO,
    name="PurgeIdleCheckerBindingPayload",
)
class PurgeIdleCheckerBindingPayloadGQL:
    id: UUID = gql_field(description="Purged idle checker binding ID.")
