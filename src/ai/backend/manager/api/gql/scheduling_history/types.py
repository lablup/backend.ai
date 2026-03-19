"""GraphQL types, filters, and inputs for scheduling history."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

import strawberry
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
    DeploymentHistoryOrderField as DeploymentHistoryOrderFieldEnum,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryScopeDTO,
    RouteHistoryScopeDTO,
    SessionHistoryScopeDTO,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection as OrderDirectionEnum,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    RouteHistoryOrderField as RouteHistoryOrderFieldEnum,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    SchedulingResultType as SchedulingResultTypeEnum,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    SessionHistoryOrderField as SessionHistoryOrderFieldEnum,
)
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SubStepResult,
)

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


@strawberry.enum(name="SchedulingResult", description="Scheduling result status")
class SchedulingResultGQL(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STALE = "STALE"
    NEED_RETRY = "NEED_RETRY"
    EXPIRED = "EXPIRED"
    GIVE_UP = "GIVE_UP"
    SKIPPED = "SKIPPED"

    @classmethod
    def from_internal(cls, value: SchedulingResult) -> SchedulingResultGQL:
        match value:
            case SchedulingResult.SUCCESS:
                return cls.SUCCESS
            case SchedulingResult.FAILURE:
                return cls.FAILURE
            case SchedulingResult.STALE:
                return cls.STALE
            case SchedulingResult.NEED_RETRY:
                return cls.NEED_RETRY
            case SchedulingResult.EXPIRED:
                return cls.EXPIRED
            case SchedulingResult.GIVE_UP:
                return cls.GIVE_UP
            case SchedulingResult.SKIPPED:
                return cls.SKIPPED
            case _:
                raise ValueError(f"Unknown SchedulingResult: {value}")

    def to_internal(self) -> SchedulingResult:
        match self:
            case SchedulingResultGQL.SUCCESS:
                return SchedulingResult.SUCCESS
            case SchedulingResultGQL.FAILURE:
                return SchedulingResult.FAILURE
            case SchedulingResultGQL.STALE:
                return SchedulingResult.STALE
            case SchedulingResultGQL.NEED_RETRY:
                return SchedulingResult.NEED_RETRY
            case SchedulingResultGQL.EXPIRED:
                return SchedulingResult.EXPIRED
            case SchedulingResultGQL.GIVE_UP:
                return SchedulingResult.GIVE_UP
            case SchedulingResultGQL.SKIPPED:
                return SchedulingResult.SKIPPED


@strawberry.enum
class SessionSchedulingHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.enum
class DeploymentHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.enum
class RouteHistoryOrderField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# Types


@gql_node_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Sub-step result in scheduling history.")
)
class SubStepResultGQL:
    step: str
    result: SchedulingResultGQL
    error_code: str | None
    message: str | None
    started_at: datetime | None
    ended_at: datetime | None

    @classmethod
    def from_dataclass(cls, data: SubStepResult) -> Self:
        return cls(
            step=data.step,
            result=SchedulingResultGQL.from_internal(data.result),
            error_code=data.error_code,
            message=data.message,
            started_at=data.started_at,
            ended_at=data.ended_at,
        )


@gql_node_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Session scheduling history record.")
)
class SessionSchedulingHistory(PydanticNodeMixin[SessionHistoryNode]):
    id: NodeID[str]
    _session_id: strawberry.Private[UUID]
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

    @strawberry.field(description="The session ID this history record belongs to.")  # type: ignore[misc]
    def session_id(self) -> ID:
        return ID(str(self._session_id))

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.session_history_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_pydantic(
        cls,
        dto: SessionHistoryNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        return cls(
            id=ID(str(dto.id)),
            _session_id=dto.session_id,
            phase=dto.phase,
            from_status=dto.from_status,
            to_status=dto.to_status,
            result=SchedulingResultGQL(dto.result),
            error_code=dto.error_code,
            message=dto.message,
            sub_steps=[
                SubStepResultGQL(
                    step=s.step,
                    result=SchedulingResultGQL(s.result),
                    error_code=s.error_code,
                    message=s.message,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                )
                for s in dto.sub_steps
            ],
            attempts=dto.attempts,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    @classmethod
    def from_dataclass(cls, data: SessionSchedulingHistoryData) -> Self:
        return cls(
            id=ID(str(data.id)),
            _session_id=data.session_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=SchedulingResultGQL.from_internal(data.result),
            error_code=data.error_code,
            message=data.message,
            sub_steps=[SubStepResultGQL.from_dataclass(s) for s in data.sub_steps],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


@gql_node_type(BackendAIGQLMeta(added_version="26.3.0", description="Deployment history record."))
class DeploymentHistory(PydanticNodeMixin[DeploymentHistoryNode]):
    id: NodeID[str]
    _deployment_id: strawberry.Private[UUID]
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

    @strawberry.field(description="The deployment ID this history record belongs to.")  # type: ignore[misc]
    def deployment_id(self) -> ID:
        return ID(str(self._deployment_id))

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.deployment_history_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_pydantic(
        cls,
        dto: DeploymentHistoryNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        return cls(
            id=ID(str(dto.id)),
            _deployment_id=dto.deployment_id,
            phase=dto.phase,
            from_status=dto.from_status,
            to_status=dto.to_status,
            result=SchedulingResultGQL(dto.result),
            error_code=dto.error_code,
            message=dto.message,
            sub_steps=[
                SubStepResultGQL(
                    step=s.step,
                    result=SchedulingResultGQL(s.result),
                    error_code=s.error_code,
                    message=s.message,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                )
                for s in dto.sub_steps
            ],
            attempts=dto.attempts,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    @classmethod
    def from_dataclass(cls, data: DeploymentHistoryData) -> Self:
        return cls(
            id=ID(str(data.id)),
            _deployment_id=data.deployment_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=SchedulingResultGQL.from_internal(data.result),
            error_code=data.error_code,
            message=data.message,
            sub_steps=[SubStepResultGQL.from_dataclass(s) for s in data.sub_steps],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


@gql_node_type(BackendAIGQLMeta(added_version="26.3.0", description="Route history record."))
class RouteHistory(PydanticNodeMixin[RouteHistoryNode]):
    id: NodeID[str]
    _route_id: strawberry.Private[UUID]
    _deployment_id: strawberry.Private[UUID]
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

    @strawberry.field(description="The route ID this history record belongs to.")  # type: ignore[misc]
    def route_id(self) -> ID:
        return ID(str(self._route_id))

    @strawberry.field(description="The deployment ID this route belongs to.")  # type: ignore[misc]
    def deployment_id(self) -> ID:
        return ID(str(self._deployment_id))

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.route_history_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_pydantic(
        cls,
        dto: RouteHistoryNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        return cls(
            id=ID(str(dto.id)),
            _route_id=dto.route_id,
            _deployment_id=dto.deployment_id,
            phase=dto.phase,
            from_status=dto.from_status,
            to_status=dto.to_status,
            result=SchedulingResultGQL(dto.result),
            error_code=dto.error_code,
            message=dto.message,
            sub_steps=[
                SubStepResultGQL(
                    step=s.step,
                    result=SchedulingResultGQL(s.result),
                    error_code=s.error_code,
                    message=s.message,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                )
                for s in dto.sub_steps
            ],
            attempts=dto.attempts,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    @classmethod
    def from_dataclass(cls, data: RouteHistoryData) -> Self:
        return cls(
            id=ID(str(data.id)),
            _route_id=data.route_id,
            _deployment_id=data.deployment_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=SchedulingResultGQL.from_internal(data.result),
            error_code=data.error_code,
            message=data.message,
            sub_steps=[SubStepResultGQL.from_dataclass(s) for s in data.sub_steps],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


# Scope input types (added in 26.2.0)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for session scheduling history query", added_version="24.09.0"
    ),
    model=SessionHistoryScopeDTO,
    name="SessionScope",
)
class SessionScope:
    """Scope for session-level scheduling history queries."""

    session_id: UUID = strawberry.field(description="Session ID to get history for")

    def to_pydantic(self) -> SessionHistoryScopeDTO:
        return SessionHistoryScopeDTO(session_id=self.session_id)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for deployment scheduling history query", added_version="24.09.0"
    ),
    model=DeploymentHistoryScopeDTO,
    name="DeploymentScope",
)
class DeploymentScope:
    """Scope for deployment-level scheduling history queries."""

    deployment_id: UUID = strawberry.field(description="Deployment ID to get history for")

    def to_pydantic(self) -> DeploymentHistoryScopeDTO:
        return DeploymentHistoryScopeDTO(deployment_id=self.deployment_id)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for route scheduling history query", added_version="24.09.0"
    ),
    model=RouteHistoryScopeDTO,
    name="RouteScope",
)
class RouteScope:
    """Scope for route-level scheduling history queries."""

    route_id: UUID = strawberry.field(description="Route ID to get history for")

    def to_pydantic(self) -> RouteHistoryScopeDTO:
        return RouteHistoryScopeDTO(route_id=self.route_id)


# Filters and orders (pydantic-backed inputs)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for scheduling result with equality and membership operators.",
        added_version="26.3.0",
    ),
    model=SchedulingResultFilterDTO,
    name="SchedulingResultFilter",
)
class SchedulingResultFilterGQL:
    equals: SchedulingResultGQL | None = None
    in_: list[SchedulingResultGQL] | None = strawberry.field(name="in", default=None)
    not_equals: SchedulingResultGQL | None = None
    not_in: list[SchedulingResultGQL] | None = None

    def to_pydantic(self) -> SchedulingResultFilterDTO:
        return SchedulingResultFilterDTO(
            equals=SchedulingResultTypeEnum(self.equals.value) if self.equals else None,
            in_=[SchedulingResultTypeEnum(v.value) for v in self.in_] if self.in_ else None,
            not_equals=SchedulingResultTypeEnum(self.not_equals.value) if self.not_equals else None,
            not_in=[SchedulingResultTypeEnum(v.value) for v in self.not_in]
            if self.not_in
            else None,
        )


@strawberry.input(
    name="SessionSchedulingHistoryFilter",
    description="Added in 24.09.0. Filter for session scheduling history",
)
class SessionSchedulingHistoryFilter:
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

    def to_pydantic(self) -> SessionHistoryFilterDTO:
        return SessionHistoryFilterDTO(
            id=self.id.to_pydantic() if self.id else None,
            session_id=self.session_id.to_pydantic() if self.session_id else None,
            phase=self.phase.to_pydantic() if self.phase else None,
            from_status=self.from_status,
            to_status=self.to_status,
            result=self.result.to_pydantic() if self.result else None,
            error_code=self.error_code.to_pydantic() if self.error_code else None,
            message=self.message.to_pydantic() if self.message else None,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            updated_at=self.updated_at.to_pydantic() if self.updated_at else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for session scheduling history", added_version="24.09.0"
    ),
    model=SessionHistoryOrderDTO,
    name="SessionSchedulingHistoryOrderBy",
)
class SessionSchedulingHistoryOrderBy:
    field: SessionSchedulingHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> SessionHistoryOrderDTO:
        return SessionHistoryOrderDTO(
            field=SessionHistoryOrderFieldEnum(self.field.value),
            direction=OrderDirectionEnum(self.direction.value),
        )


@strawberry.input(
    name="DeploymentHistoryFilter",
    description="Added in 24.09.0. Filter for deployment history",
)
class DeploymentHistoryFilter:
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

    def to_pydantic(self) -> DeploymentHistoryFilterDTO:
        return DeploymentHistoryFilterDTO(
            id=self.id.to_pydantic() if self.id else None,
            deployment_id=self.deployment_id.to_pydantic() if self.deployment_id else None,
            phase=self.phase.to_pydantic() if self.phase else None,
            from_status=self.from_status,
            to_status=self.to_status,
            result=self.result.to_pydantic() if self.result else None,
            error_code=self.error_code.to_pydantic() if self.error_code else None,
            message=self.message.to_pydantic() if self.message else None,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            updated_at=self.updated_at.to_pydantic() if self.updated_at else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for deployment history", added_version="24.09.0"
    ),
    model=DeploymentHistoryOrderDTO,
    name="DeploymentHistoryOrderBy",
)
class DeploymentHistoryOrderBy:
    field: DeploymentHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> DeploymentHistoryOrderDTO:
        return DeploymentHistoryOrderDTO(
            field=DeploymentHistoryOrderFieldEnum(self.field.value),
            direction=OrderDirectionEnum(self.direction.value),
        )


@strawberry.input(
    name="RouteHistoryFilter",
    description="Added in 24.09.0. Filter for route history",
)
class RouteHistoryFilter:
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

    def to_pydantic(self) -> RouteHistoryFilterDTO:
        return RouteHistoryFilterDTO(
            id=self.id.to_pydantic() if self.id else None,
            route_id=self.route_id.to_pydantic() if self.route_id else None,
            deployment_id=self.deployment_id.to_pydantic() if self.deployment_id else None,
            phase=self.phase.to_pydantic() if self.phase else None,
            from_status=self.from_status,
            to_status=self.to_status,
            result=self.result.to_pydantic() if self.result else None,
            error_code=self.error_code.to_pydantic() if self.error_code else None,
            message=self.message.to_pydantic() if self.message else None,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            updated_at=self.updated_at.to_pydantic() if self.updated_at else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for route history", added_version="24.09.0"
    ),
    model=RouteHistoryOrderDTO,
    name="RouteHistoryOrderBy",
)
class RouteHistoryOrderBy:
    field: RouteHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> RouteHistoryOrderDTO:
        return RouteHistoryOrderDTO(
            field=RouteHistoryOrderFieldEnum(self.field.value),
            direction=OrderDirectionEnum(self.direction.value),
        )
