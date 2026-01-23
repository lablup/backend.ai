"""GraphQL types, filters, and inputs for scheduling history."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Optional, Self, override
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SubStepResult,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.scheduling_history.options import (
    DeploymentHistoryConditions,
    DeploymentHistoryOrders,
    RouteHistoryConditions,
    RouteHistoryOrders,
    SessionSchedulingHistoryConditions,
    SessionSchedulingHistoryOrders,
)

__all__ = (
    # Enums
    "SchedulingResultGQL",
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
)


# Enums


@strawberry.enum(name="SchedulingResult", description="Scheduling result status")
class SchedulingResultGQL(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STALE = "STALE"

    @classmethod
    def from_internal(cls, value: SchedulingResult) -> SchedulingResultGQL:
        match value:
            case SchedulingResult.SUCCESS:
                return cls.SUCCESS
            case SchedulingResult.FAILURE:
                return cls.FAILURE
            case SchedulingResult.STALE:
                return cls.STALE
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


@strawberry.type(description="Sub-step result in scheduling history")
class SubStepResultGQL:
    step: str
    result: SchedulingResultGQL
    error_code: Optional[str]
    message: Optional[str]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

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


@strawberry.type(description="Session scheduling history record")
class SessionSchedulingHistory(Node):
    id: NodeID[str]
    _session_id: strawberry.Private[UUID]
    phase: str
    from_status: Optional[str]
    to_status: Optional[str]
    result: SchedulingResultGQL
    error_code: Optional[str]
    message: Optional[str]
    sub_steps: list[SubStepResultGQL]
    attempts: int
    created_at: datetime
    updated_at: datetime

    @strawberry.field(description="The session ID this history record belongs to.")
    def session_id(self) -> ID:
        return ID(str(self._session_id))

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


@strawberry.type(description="Deployment history record")
class DeploymentHistory(Node):
    id: NodeID[str]
    _deployment_id: strawberry.Private[UUID]
    phase: str
    from_status: Optional[str]
    to_status: Optional[str]
    result: SchedulingResultGQL
    error_code: Optional[str]
    message: Optional[str]
    sub_steps: list[SubStepResultGQL]
    attempts: int
    created_at: datetime
    updated_at: datetime

    @strawberry.field(description="The deployment ID this history record belongs to.")
    def deployment_id(self) -> ID:
        return ID(str(self._deployment_id))

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


@strawberry.type(description="Route history record")
class RouteHistory(Node):
    id: NodeID[str]
    _route_id: strawberry.Private[UUID]
    _deployment_id: strawberry.Private[UUID]
    phase: str
    from_status: Optional[str]
    to_status: Optional[str]
    result: SchedulingResultGQL
    error_code: Optional[str]
    message: Optional[str]
    sub_steps: list[SubStepResultGQL]
    attempts: int
    created_at: datetime
    updated_at: datetime

    @strawberry.field(description="The route ID this history record belongs to.")
    def route_id(self) -> ID:
        return ID(str(self._route_id))

    @strawberry.field(description="The deployment ID this route belongs to.")
    def deployment_id(self) -> ID:
        return ID(str(self._deployment_id))

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


# Filters


@strawberry.input(description="Filter for session scheduling history")
class SessionSchedulingHistoryFilter(GQLFilter):
    id: Optional[UUIDFilter] = None
    session_id: Optional[UUIDFilter] = None
    phase: Optional[StringFilter] = None
    from_status: Optional[list[str]] = None
    to_status: Optional[list[str]] = None
    result: Optional[list[SchedulingResultGQL]] = None
    error_code: Optional[StringFilter] = None
    message: Optional[StringFilter] = None
    created_at: Optional[DateTimeFilter] = None
    updated_at: Optional[DateTimeFilter] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        conditions: list[QueryCondition] = []

        if self.id is not None:
            condition = self.id.build_query_condition(
                equals_factory=SessionSchedulingHistoryConditions.by_id_filter,
                in_factory=SessionSchedulingHistoryConditions.by_id_in,
            )
            if condition:
                conditions.append(condition)

        if self.session_id is not None:
            condition = self.session_id.build_query_condition(
                equals_factory=SessionSchedulingHistoryConditions.by_session_id_filter,
                in_factory=SessionSchedulingHistoryConditions.by_session_id_in,
            )
            if condition:
                conditions.append(condition)

        if self.phase is not None:
            condition = self.phase.build_query_condition(
                contains_factory=SessionSchedulingHistoryConditions.by_phase_contains,
                equals_factory=SessionSchedulingHistoryConditions.by_phase_equals,
                starts_with_factory=SessionSchedulingHistoryConditions.by_phase_starts_with,
                ends_with_factory=SessionSchedulingHistoryConditions.by_phase_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.from_status is not None and len(self.from_status) > 0:
            conditions.append(SessionSchedulingHistoryConditions.by_from_statuses(self.from_status))

        if self.to_status is not None and len(self.to_status) > 0:
            conditions.append(SessionSchedulingHistoryConditions.by_to_statuses(self.to_status))

        if self.result is not None and len(self.result) > 0:
            conditions.append(
                SessionSchedulingHistoryConditions.by_results([
                    r.to_internal() for r in self.result
                ])
            )

        if self.error_code is not None:
            condition = self.error_code.build_query_condition(
                contains_factory=SessionSchedulingHistoryConditions.by_error_code_contains,
                equals_factory=SessionSchedulingHistoryConditions.by_error_code_equals,
                starts_with_factory=SessionSchedulingHistoryConditions.by_error_code_starts_with,
                ends_with_factory=SessionSchedulingHistoryConditions.by_error_code_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.message is not None:
            condition = self.message.build_query_condition(
                contains_factory=SessionSchedulingHistoryConditions.by_message_contains,
                equals_factory=SessionSchedulingHistoryConditions.by_message_equals,
                starts_with_factory=SessionSchedulingHistoryConditions.by_message_starts_with,
                ends_with_factory=SessionSchedulingHistoryConditions.by_message_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.created_at is not None:
            condition = self.created_at.build_query_condition(
                before_factory=SessionSchedulingHistoryConditions.by_created_at_before,
                after_factory=SessionSchedulingHistoryConditions.by_created_at_after,
                equals_factory=SessionSchedulingHistoryConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)

        if self.updated_at is not None:
            condition = self.updated_at.build_query_condition(
                before_factory=SessionSchedulingHistoryConditions.by_updated_at_before,
                after_factory=SessionSchedulingHistoryConditions.by_updated_at_after,
                equals_factory=SessionSchedulingHistoryConditions.by_updated_at_equals,
            )
            if condition:
                conditions.append(condition)

        return conditions


@strawberry.input(description="Order by specification for session scheduling history")
class SessionSchedulingHistoryOrderBy(GQLOrderBy):
    field: SessionSchedulingHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case SessionSchedulingHistoryOrderField.CREATED_AT:
                return SessionSchedulingHistoryOrders.created_at(ascending)
            case SessionSchedulingHistoryOrderField.UPDATED_AT:
                return SessionSchedulingHistoryOrders.updated_at(ascending)


@strawberry.input(description="Filter for deployment history")
class DeploymentHistoryFilter(GQLFilter):
    id: Optional[UUIDFilter] = None
    deployment_id: Optional[UUIDFilter] = None
    phase: Optional[StringFilter] = None
    from_status: Optional[list[str]] = None
    to_status: Optional[list[str]] = None
    result: Optional[list[SchedulingResultGQL]] = None
    error_code: Optional[StringFilter] = None
    message: Optional[StringFilter] = None
    created_at: Optional[DateTimeFilter] = None
    updated_at: Optional[DateTimeFilter] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        conditions: list[QueryCondition] = []

        if self.id is not None:
            condition = self.id.build_query_condition(
                equals_factory=DeploymentHistoryConditions.by_id_filter,
                in_factory=DeploymentHistoryConditions.by_id_in,
            )
            if condition:
                conditions.append(condition)

        if self.deployment_id is not None:
            condition = self.deployment_id.build_query_condition(
                equals_factory=DeploymentHistoryConditions.by_deployment_id_filter,
                in_factory=DeploymentHistoryConditions.by_deployment_id_in,
            )
            if condition:
                conditions.append(condition)

        if self.phase is not None:
            condition = self.phase.build_query_condition(
                contains_factory=DeploymentHistoryConditions.by_phase_contains,
                equals_factory=DeploymentHistoryConditions.by_phase_equals,
                starts_with_factory=DeploymentHistoryConditions.by_phase_starts_with,
                ends_with_factory=DeploymentHistoryConditions.by_phase_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.from_status is not None and len(self.from_status) > 0:
            conditions.append(DeploymentHistoryConditions.by_from_statuses(self.from_status))

        if self.to_status is not None and len(self.to_status) > 0:
            conditions.append(DeploymentHistoryConditions.by_to_statuses(self.to_status))

        if self.result is not None and len(self.result) > 0:
            conditions.append(
                DeploymentHistoryConditions.by_results([r.to_internal() for r in self.result])
            )

        if self.error_code is not None:
            condition = self.error_code.build_query_condition(
                contains_factory=DeploymentHistoryConditions.by_error_code_contains,
                equals_factory=DeploymentHistoryConditions.by_error_code_equals,
                starts_with_factory=DeploymentHistoryConditions.by_error_code_starts_with,
                ends_with_factory=DeploymentHistoryConditions.by_error_code_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.message is not None:
            condition = self.message.build_query_condition(
                contains_factory=DeploymentHistoryConditions.by_message_contains,
                equals_factory=DeploymentHistoryConditions.by_message_equals,
                starts_with_factory=DeploymentHistoryConditions.by_message_starts_with,
                ends_with_factory=DeploymentHistoryConditions.by_message_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.created_at is not None:
            condition = self.created_at.build_query_condition(
                before_factory=DeploymentHistoryConditions.by_created_at_before,
                after_factory=DeploymentHistoryConditions.by_created_at_after,
                equals_factory=DeploymentHistoryConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)

        if self.updated_at is not None:
            condition = self.updated_at.build_query_condition(
                before_factory=DeploymentHistoryConditions.by_updated_at_before,
                after_factory=DeploymentHistoryConditions.by_updated_at_after,
                equals_factory=DeploymentHistoryConditions.by_updated_at_equals,
            )
            if condition:
                conditions.append(condition)

        return conditions


@strawberry.input(description="Order by specification for deployment history")
class DeploymentHistoryOrderBy(GQLOrderBy):
    field: DeploymentHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case DeploymentHistoryOrderField.CREATED_AT:
                return DeploymentHistoryOrders.created_at(ascending)
            case DeploymentHistoryOrderField.UPDATED_AT:
                return DeploymentHistoryOrders.updated_at(ascending)


@strawberry.input(description="Filter for route history")
class RouteHistoryFilter(GQLFilter):
    id: Optional[UUIDFilter] = None
    route_id: Optional[UUIDFilter] = None
    deployment_id: Optional[UUIDFilter] = None
    phase: Optional[StringFilter] = None
    from_status: Optional[list[str]] = None
    to_status: Optional[list[str]] = None
    result: Optional[list[SchedulingResultGQL]] = None
    error_code: Optional[StringFilter] = None
    message: Optional[StringFilter] = None
    created_at: Optional[DateTimeFilter] = None
    updated_at: Optional[DateTimeFilter] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        conditions: list[QueryCondition] = []

        if self.id is not None:
            condition = self.id.build_query_condition(
                equals_factory=RouteHistoryConditions.by_id_filter,
                in_factory=RouteHistoryConditions.by_id_in,
            )
            if condition:
                conditions.append(condition)

        if self.route_id is not None:
            condition = self.route_id.build_query_condition(
                equals_factory=RouteHistoryConditions.by_route_id_filter,
                in_factory=RouteHistoryConditions.by_route_id_in,
            )
            if condition:
                conditions.append(condition)

        if self.deployment_id is not None:
            condition = self.deployment_id.build_query_condition(
                equals_factory=RouteHistoryConditions.by_deployment_id_filter,
                in_factory=RouteHistoryConditions.by_deployment_id_in,
            )
            if condition:
                conditions.append(condition)

        if self.phase is not None:
            condition = self.phase.build_query_condition(
                contains_factory=RouteHistoryConditions.by_phase_contains,
                equals_factory=RouteHistoryConditions.by_phase_equals,
                starts_with_factory=RouteHistoryConditions.by_phase_starts_with,
                ends_with_factory=RouteHistoryConditions.by_phase_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.from_status is not None and len(self.from_status) > 0:
            conditions.append(RouteHistoryConditions.by_from_statuses(self.from_status))

        if self.to_status is not None and len(self.to_status) > 0:
            conditions.append(RouteHistoryConditions.by_to_statuses(self.to_status))

        if self.result is not None and len(self.result) > 0:
            conditions.append(
                RouteHistoryConditions.by_results([r.to_internal() for r in self.result])
            )

        if self.error_code is not None:
            condition = self.error_code.build_query_condition(
                contains_factory=RouteHistoryConditions.by_error_code_contains,
                equals_factory=RouteHistoryConditions.by_error_code_equals,
                starts_with_factory=RouteHistoryConditions.by_error_code_starts_with,
                ends_with_factory=RouteHistoryConditions.by_error_code_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.message is not None:
            condition = self.message.build_query_condition(
                contains_factory=RouteHistoryConditions.by_message_contains,
                equals_factory=RouteHistoryConditions.by_message_equals,
                starts_with_factory=RouteHistoryConditions.by_message_starts_with,
                ends_with_factory=RouteHistoryConditions.by_message_ends_with,
            )
            if condition:
                conditions.append(condition)

        if self.created_at is not None:
            condition = self.created_at.build_query_condition(
                before_factory=RouteHistoryConditions.by_created_at_before,
                after_factory=RouteHistoryConditions.by_created_at_after,
                equals_factory=RouteHistoryConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)

        if self.updated_at is not None:
            condition = self.updated_at.build_query_condition(
                before_factory=RouteHistoryConditions.by_updated_at_before,
                after_factory=RouteHistoryConditions.by_updated_at_after,
                equals_factory=RouteHistoryConditions.by_updated_at_equals,
            )
            if condition:
                conditions.append(condition)

        return conditions


@strawberry.input(description="Order by specification for route history")
class RouteHistoryOrderBy(GQLOrderBy):
    field: RouteHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case RouteHistoryOrderField.CREATED_AT:
                return RouteHistoryOrders.created_at(ascending)
            case RouteHistoryOrderField.UPDATED_AT:
                return RouteHistoryOrders.updated_at(ascending)
