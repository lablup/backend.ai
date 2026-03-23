"""GraphQL types, filters, and inputs for scheduling history."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Self, cast
from uuid import UUID

from strawberry import ID, Info
from strawberry.relay import NodeID

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    DeploymentHistoryFilter as DeploymentHistoryFilterDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    DeploymentHistoryOrder as DeploymentHistoryOrderDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    RouteHistoryFilter as RouteHistoryFilterDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    RouteHistoryOrder as RouteHistoryOrderDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    SchedulingResultFilter as SchedulingResultFilterDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    SessionHistoryFilter as SessionHistoryFilterDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    SessionHistoryOrder as SessionHistoryOrderDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    DeploymentHistoryNode,
    RouteHistoryNode,
    SessionHistoryNode,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryScopeDTO,
    RouteHistoryScopeDTO,
    SessionHistoryScopeDTO,
    SubStepResultInfo,
)
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
    # Enums
    "SchedulingResultGQL",
    # Filter wrappers
    "SchedulingResultFilterGQL",
    "SessionSchedulingHistoryOrderField",
    "DeploymentHistoryOrderField",
    "RouteHistoryOrderField",
    # Types
    "SubStepResultGQL",
    "SessionSchedulingHistory",
    "DeploymentHistory",
    "RouteHistory",
    # Filters
    "SessionSchedulingHistoryFilter",
    "SessionSchedulingHistoryOrderBy",
    "DeploymentHistoryFilter",
    "DeploymentHistoryOrderBy",
    "RouteHistoryFilter",
    "RouteHistoryOrderBy",
    # Scope types (added in 26.2.0)
    "SessionScope",
    "DeploymentScope",
    "RouteScope",
)


# Enums


@gql_enum(
    BackendAIGQLMeta(added_version="26.3.0", description="Scheduling result status"),
    name="SchedulingResult",
)
class SchedulingResultGQL(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STALE = "STALE"
    NEED_RETRY = "NEED_RETRY"
    EXPIRED = "EXPIRED"
    GIVE_UP = "GIVE_UP"
    SKIPPED = "SKIPPED"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering session scheduling history",
    )
)
class SessionSchedulingHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Fields available for ordering deployment history",
    )
)
class DeploymentHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Fields available for ordering route history"
    )
)
class RouteHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# Types


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Sub-step result in scheduling history.",
    ),
    model=SubStepResultInfo,
    name="SubStepResult",
)
class SubStepResultGQL(PydanticOutputMixin[SubStepResultInfo]):
    step: str
    result: SchedulingResultGQL
    error_code: str | None
    message: str | None
    started_at: datetime | None
    ended_at: datetime | None


@gql_node_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Session scheduling history record.")
)
class SessionSchedulingHistory(PydanticNodeMixin[SessionHistoryNode]):
    id: NodeID[str]
    session_id: ID
    phase: str
    from_status: str | None
    to_status: str | None
    result: SchedulingResultGQL
    error_code: str | None
    message: str | None
    sub_steps: list[SubStepResultGQL]
    attempts: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader returns GQL type instances directly via from_pydantic adapter.
        results = await info.context.data_loaders.session_history_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


@gql_node_type(BackendAIGQLMeta(added_version="26.3.0", description="Deployment history record."))
class DeploymentHistory(PydanticNodeMixin[DeploymentHistoryNode]):
    id: NodeID[str]
    deployment_id: ID
    phase: str
    from_status: str | None
    to_status: str | None
    result: SchedulingResultGQL
    error_code: str | None
    message: str | None
    sub_steps: list[SubStepResultGQL]
    attempts: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader returns GQL type instances directly via from_pydantic adapter.
        results = await info.context.data_loaders.deployment_history_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


@gql_node_type(BackendAIGQLMeta(added_version="26.3.0", description="Route history record."))
class RouteHistory(PydanticNodeMixin[RouteHistoryNode]):
    id: NodeID[str]
    route_id: ID
    deployment_id: ID
    phase: str
    from_status: str | None
    to_status: str | None
    result: SchedulingResultGQL
    error_code: str | None
    message: str | None
    sub_steps: list[SubStepResultGQL]
    attempts: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # DataLoader returns GQL type instances directly via from_pydantic adapter.
        results = await info.context.data_loaders.route_history_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


# Scope input types (added in 26.2.0)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for session scheduling history query", added_version="24.09.0"
    ),
    name="SessionScope",
)
class SessionScope(PydanticInputMixin[SessionHistoryScopeDTO]):
    """Scope for session-level scheduling history queries."""

    session_id: UUID = gql_field(description="Session ID to get history for")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for deployment scheduling history query", added_version="24.09.0"
    ),
    name="DeploymentScope",
)
class DeploymentScope(PydanticInputMixin[DeploymentHistoryScopeDTO]):
    """Scope for deployment-level scheduling history queries."""

    deployment_id: UUID = gql_field(description="Deployment ID to get history for")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for route scheduling history query", added_version="24.09.0"
    ),
    name="RouteScope",
)
class RouteScope(PydanticInputMixin[RouteHistoryScopeDTO]):
    """Scope for route-level scheduling history queries."""

    route_id: UUID = gql_field(description="Route ID to get history for")


# Filters and orders (pydantic-backed inputs)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for scheduling result with equality and membership operators.",
        added_version="26.3.0",
    ),
    name="SchedulingResultFilter",
)
class SchedulingResultFilterGQL(PydanticInputMixin[SchedulingResultFilterDTO]):
    equals: SchedulingResultGQL | None = None
    in_: list[SchedulingResultGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_equals: SchedulingResultGQL | None = None
    not_in: list[SchedulingResultGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for session scheduling history", added_version="24.09.0"),
    name="SessionSchedulingHistoryFilter",
)
class SessionSchedulingHistoryFilter(PydanticInputMixin[SessionHistoryFilterDTO]):
    id: UUIDFilter | None = None
    session_id: UUIDFilter | None = None
    phase: StringFilter | None = None
    from_status: list[str] | None = None
    to_status: list[str] | None = None
    result: SchedulingResultFilterGQL | None = None
    error_code: StringFilter | None = None
    message: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    updated_at: DateTimeFilter | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for session scheduling history", added_version="24.09.0"
    ),
    name="SessionSchedulingHistoryOrderBy",
)
class SessionSchedulingHistoryOrderBy(PydanticInputMixin[SessionHistoryOrderDTO]):
    field: SessionSchedulingHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for deployment history", added_version="24.09.0"),
    name="DeploymentHistoryFilter",
)
class DeploymentHistoryFilter(PydanticInputMixin[DeploymentHistoryFilterDTO]):
    id: UUIDFilter | None = None
    deployment_id: UUIDFilter | None = None
    phase: StringFilter | None = None
    from_status: list[str] | None = None
    to_status: list[str] | None = None
    result: SchedulingResultFilterGQL | None = None
    error_code: StringFilter | None = None
    message: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    updated_at: DateTimeFilter | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for deployment history", added_version="24.09.0"
    ),
    name="DeploymentHistoryOrderBy",
)
class DeploymentHistoryOrderBy(PydanticInputMixin[DeploymentHistoryOrderDTO]):
    field: DeploymentHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for route history", added_version="24.09.0"),
    name="RouteHistoryFilter",
)
class RouteHistoryFilter(PydanticInputMixin[RouteHistoryFilterDTO]):
    id: UUIDFilter | None = None
    route_id: UUIDFilter | None = None
    deployment_id: UUIDFilter | None = None
    phase: StringFilter | None = None
    from_status: list[str] | None = None
    to_status: list[str] | None = None
    result: SchedulingResultFilterGQL | None = None
    error_code: StringFilter | None = None
    message: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    updated_at: DateTimeFilter | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for route history", added_version="24.09.0"
    ),
    name="RouteHistoryOrderBy",
)
class RouteHistoryOrderBy(PydanticInputMixin[RouteHistoryOrderDTO]):
    field: RouteHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC
