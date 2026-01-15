"""
Adapters to convert scheduling history DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.scheduling_history import (
    DeploymentHistoryDTO,
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryDTO,
    RouteHistoryFilter,
    RouteHistoryOrder,
    RouteHistoryOrderField,
    SchedulingResultType,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
    SessionHistoryDTO,
    SessionHistoryFilter,
    SessionHistoryOrder,
    SessionHistoryOrderField,
    SubStepResultDTO,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SubStepResult,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.scheduling_history.options import (
    DeploymentHistoryConditions,
    DeploymentHistoryOrders,
    RouteHistoryConditions,
    RouteHistoryOrders,
    SessionSchedulingHistoryConditions,
    SessionSchedulingHistoryOrders,
)

__all__ = ("SchedulingHistoryAdapter",)


class SchedulingHistoryAdapter(BaseFilterAdapter):
    """Adapter for converting scheduling history requests to repository queries."""

    # Session History

    def build_session_history_querier(self, request: SearchSessionHistoryRequest) -> BatchQuerier:
        """Build a BatchQuerier for session scheduling history from search request."""
        conditions = self._convert_session_filter(request.filter) if request.filter else []
        orders = [self._convert_session_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_session_filter(self, filter: SessionHistoryFilter) -> list[QueryCondition]:
        """Convert session history filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.session_id is not None:
            condition = self.convert_uuid_filter(
                filter.session_id,
                equals_factory=SessionSchedulingHistoryConditions.by_session_id_filter,
                in_factory=SessionSchedulingHistoryConditions.by_session_id_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.phase is not None:
            condition = self.convert_string_filter(
                filter.phase,
                contains_factory=SessionSchedulingHistoryConditions.by_phase_contains,
                equals_factory=SessionSchedulingHistoryConditions.by_phase_equals,
                starts_with_factory=SessionSchedulingHistoryConditions.by_phase_starts_with,
                ends_with_factory=SessionSchedulingHistoryConditions.by_phase_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.from_status is not None and len(filter.from_status) > 0:
            conditions.append(
                SessionSchedulingHistoryConditions.by_from_statuses(filter.from_status)
            )

        if filter.to_status is not None and len(filter.to_status) > 0:
            conditions.append(
                SessionSchedulingHistoryConditions.by_to_statuses(filter.to_status)
            )

        if filter.result is not None and len(filter.result) > 0:
            conditions.append(
                SessionSchedulingHistoryConditions.by_results([
                    self._convert_result_type(r) for r in filter.result
                ])
            )

        if filter.error_code is not None:
            condition = self.convert_string_filter(
                filter.error_code,
                contains_factory=SessionSchedulingHistoryConditions.by_error_code_contains,
                equals_factory=SessionSchedulingHistoryConditions.by_error_code_equals,
                starts_with_factory=SessionSchedulingHistoryConditions.by_error_code_starts_with,
                ends_with_factory=SessionSchedulingHistoryConditions.by_error_code_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.message is not None:
            condition = self.convert_string_filter(
                filter.message,
                contains_factory=SessionSchedulingHistoryConditions.by_message_contains,
                equals_factory=SessionSchedulingHistoryConditions.by_message_equals,
                starts_with_factory=SessionSchedulingHistoryConditions.by_message_starts_with,
                ends_with_factory=SessionSchedulingHistoryConditions.by_message_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_session_order(self, order: SessionHistoryOrder) -> QueryOrder:
        """Convert session history order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case SessionHistoryOrderField.CREATED_AT:
                return SessionSchedulingHistoryOrders.created_at(ascending=ascending)
            case SessionHistoryOrderField.UPDATED_AT:
                return SessionSchedulingHistoryOrders.updated_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_session_history_to_dto(
        self, data: SessionSchedulingHistoryData
    ) -> SessionHistoryDTO:
        """Convert SessionSchedulingHistoryData to DTO."""
        return SessionHistoryDTO(
            id=data.id,
            session_id=data.session_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=data.result.value,
            error_code=data.error_code,
            message=data.message,
            sub_steps=[self._convert_sub_step(s) for s in data.sub_steps],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    # Deployment History

    def build_deployment_history_querier(
        self, request: SearchDeploymentHistoryRequest
    ) -> BatchQuerier:
        """Build a BatchQuerier for deployment history from search request."""
        conditions = self._convert_deployment_filter(request.filter) if request.filter else []
        orders = [self._convert_deployment_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_deployment_filter(self, filter: DeploymentHistoryFilter) -> list[QueryCondition]:
        """Convert deployment history filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.deployment_id is not None:
            condition = self.convert_uuid_filter(
                filter.deployment_id,
                equals_factory=DeploymentHistoryConditions.by_deployment_id_filter,
                in_factory=DeploymentHistoryConditions.by_deployment_id_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.phase is not None:
            condition = self.convert_string_filter(
                filter.phase,
                contains_factory=DeploymentHistoryConditions.by_phase_contains,
                equals_factory=DeploymentHistoryConditions.by_phase_equals,
                starts_with_factory=DeploymentHistoryConditions.by_phase_starts_with,
                ends_with_factory=DeploymentHistoryConditions.by_phase_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.from_status is not None and len(filter.from_status) > 0:
            conditions.append(
                DeploymentHistoryConditions.by_from_statuses(filter.from_status)
            )

        if filter.to_status is not None and len(filter.to_status) > 0:
            conditions.append(
                DeploymentHistoryConditions.by_to_statuses(filter.to_status)
            )

        if filter.result is not None and len(filter.result) > 0:
            conditions.append(
                DeploymentHistoryConditions.by_results([
                    self._convert_result_type(r) for r in filter.result
                ])
            )

        if filter.error_code is not None:
            condition = self.convert_string_filter(
                filter.error_code,
                contains_factory=DeploymentHistoryConditions.by_error_code_contains,
                equals_factory=DeploymentHistoryConditions.by_error_code_equals,
                starts_with_factory=DeploymentHistoryConditions.by_error_code_starts_with,
                ends_with_factory=DeploymentHistoryConditions.by_error_code_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.message is not None:
            condition = self.convert_string_filter(
                filter.message,
                contains_factory=DeploymentHistoryConditions.by_message_contains,
                equals_factory=DeploymentHistoryConditions.by_message_equals,
                starts_with_factory=DeploymentHistoryConditions.by_message_starts_with,
                ends_with_factory=DeploymentHistoryConditions.by_message_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_deployment_order(self, order: DeploymentHistoryOrder) -> QueryOrder:
        """Convert deployment history order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case DeploymentHistoryOrderField.CREATED_AT:
                return DeploymentHistoryOrders.created_at(ascending=ascending)
            case DeploymentHistoryOrderField.UPDATED_AT:
                return DeploymentHistoryOrders.updated_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_deployment_history_to_dto(
        self, data: DeploymentHistoryData
    ) -> DeploymentHistoryDTO:
        """Convert DeploymentHistoryData to DTO."""
        return DeploymentHistoryDTO(
            id=data.id,
            deployment_id=data.deployment_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=data.result.value,
            error_code=data.error_code,
            message=data.message,
            sub_steps=[self._convert_sub_step(s) for s in data.sub_steps],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    # Route History

    def build_route_history_querier(self, request: SearchRouteHistoryRequest) -> BatchQuerier:
        """Build a BatchQuerier for route history from search request."""
        conditions = self._convert_route_filter(request.filter) if request.filter else []
        orders = [self._convert_route_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_route_filter(self, filter: RouteHistoryFilter) -> list[QueryCondition]:
        """Convert route history filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.route_id is not None:
            condition = self.convert_uuid_filter(
                filter.route_id,
                equals_factory=RouteHistoryConditions.by_route_id_filter,
                in_factory=RouteHistoryConditions.by_route_id_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.deployment_id is not None:
            condition = self.convert_uuid_filter(
                filter.deployment_id,
                equals_factory=RouteHistoryConditions.by_deployment_id_filter,
                in_factory=RouteHistoryConditions.by_deployment_id_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.phase is not None:
            condition = self.convert_string_filter(
                filter.phase,
                contains_factory=RouteHistoryConditions.by_phase_contains,
                equals_factory=RouteHistoryConditions.by_phase_equals,
                starts_with_factory=RouteHistoryConditions.by_phase_starts_with,
                ends_with_factory=RouteHistoryConditions.by_phase_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.from_status is not None and len(filter.from_status) > 0:
            conditions.append(
                RouteHistoryConditions.by_from_statuses(filter.from_status)
            )

        if filter.to_status is not None and len(filter.to_status) > 0:
            conditions.append(
                RouteHistoryConditions.by_to_statuses(filter.to_status)
            )

        if filter.result is not None and len(filter.result) > 0:
            conditions.append(
                RouteHistoryConditions.by_results([
                    self._convert_result_type(r) for r in filter.result
                ])
            )

        if filter.error_code is not None:
            condition = self.convert_string_filter(
                filter.error_code,
                contains_factory=RouteHistoryConditions.by_error_code_contains,
                equals_factory=RouteHistoryConditions.by_error_code_equals,
                starts_with_factory=RouteHistoryConditions.by_error_code_starts_with,
                ends_with_factory=RouteHistoryConditions.by_error_code_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.message is not None:
            condition = self.convert_string_filter(
                filter.message,
                contains_factory=RouteHistoryConditions.by_message_contains,
                equals_factory=RouteHistoryConditions.by_message_equals,
                starts_with_factory=RouteHistoryConditions.by_message_starts_with,
                ends_with_factory=RouteHistoryConditions.by_message_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_route_order(self, order: RouteHistoryOrder) -> QueryOrder:
        """Convert route history order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case RouteHistoryOrderField.CREATED_AT:
                return RouteHistoryOrders.created_at(ascending=ascending)
            case RouteHistoryOrderField.UPDATED_AT:
                return RouteHistoryOrders.updated_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_route_history_to_dto(self, data: RouteHistoryData) -> RouteHistoryDTO:
        """Convert RouteHistoryData to DTO."""
        return RouteHistoryDTO(
            id=data.id,
            route_id=data.route_id,
            deployment_id=data.deployment_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=data.result.value,
            error_code=data.error_code,
            message=data.message,
            sub_steps=[self._convert_sub_step(s) for s in data.sub_steps],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    # Common helpers

    def _convert_result_type(self, result: SchedulingResultType) -> SchedulingResult:
        """Convert DTO result type to domain result type."""
        match result:
            case SchedulingResultType.SUCCESS:
                return SchedulingResult.SUCCESS
            case SchedulingResultType.FAILURE:
                return SchedulingResult.FAILURE
            case SchedulingResultType.STALE:
                return SchedulingResult.STALE

        raise ValueError(f"Unknown result type: {result}")

    def _convert_sub_step(self, sub_step: SubStepResult) -> SubStepResultDTO:
        """Convert SubStepResult to DTO."""
        return SubStepResultDTO(
            step=sub_step.step,
            result=sub_step.result.value,
            error_code=sub_step.error_code,
            message=sub_step.message,
            started_at=sub_step.started_at,
            ended_at=sub_step.ended_at,
        )
