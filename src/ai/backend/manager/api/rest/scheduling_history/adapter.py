"""
Adapters to convert scheduling history DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.data.filter_specs import StringInMatchSpec
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
from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SubStepResult,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.scheduling_history.deprecated_search import (
    DeprecatedDeploymentHistoryConditions,
    DeprecatedRouteHistoryConditions,
    DeprecatedSessionSchedulingHistoryConditions,
)
from ai.backend.manager.models.scheduling_history.searchable_fields import (
    DeploymentHistorySearchableFields,
    RouteHistorySearchableFields,
    SessionSchedulingHistorySearchableFields,
)
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

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
        fields = SessionSchedulingHistorySearchableFields.own
        return [
            *self.apply_uuid_filter(filter.session_id, fields.session_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._result_in(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(
                filter.message, DeprecatedSessionSchedulingHistoryConditions.message
            ),
        ]

    def _convert_session_order(self, order: SessionHistoryOrder) -> QueryOrder:
        """Convert session history order specification to query order."""
        fields = SessionSchedulingHistorySearchableFields.own
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case SessionHistoryOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case SessionHistoryOrderField.UPDATED_AT:
                return fields.updated_at.order.apply(ascending)

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
        fields = DeploymentHistorySearchableFields.own
        return [
            *self.apply_uuid_filter(filter.deployment_id, fields.deployment_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._result_in(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(
                filter.message, DeprecatedDeploymentHistoryConditions.message
            ),
        ]

    def _convert_deployment_order(self, order: DeploymentHistoryOrder) -> QueryOrder:
        """Convert deployment history order specification to query order."""
        fields = DeploymentHistorySearchableFields.own
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case DeploymentHistoryOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case DeploymentHistoryOrderField.UPDATED_AT:
                return fields.updated_at.order.apply(ascending)

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
        fields = RouteHistorySearchableFields.own
        return [
            *self.apply_uuid_filter(filter.route_id, fields.route_id.filter),
            *self.apply_uuid_filter(filter.deployment_id, fields.deployment_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._result_in(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(filter.message, DeprecatedRouteHistoryConditions.message),
        ]

    def _convert_route_order(self, order: RouteHistoryOrder) -> QueryOrder:
        """Convert route history order specification to query order."""
        fields = RouteHistorySearchableFields.own
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case RouteHistoryOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case RouteHistoryOrderField.UPDATED_AT:
                return fields.updated_at.order.apply(ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    @staticmethod
    def _status_in(
        statuses: list[str] | None, conditions: StringConditions
    ) -> list[QueryCondition]:
        """Narrow a status column to the values the request listed."""
        if not statuses:
            return []
        return [
            conditions.in_(
                StringInMatchSpec(values=statuses, case_insensitive=False, negated=False)
            )
        ]

    def _result_in(
        self,
        results: list[SchedulingResultType] | None,
        conditions: EnumConditions[SchedulingResult],
    ) -> list[QueryCondition]:
        """Narrow the result column to the values the request listed."""
        if not results:
            return []
        return [conditions.in_([self._convert_result_type(r) for r in results])]

    def convert_route_history_to_dto(self, data: RouteHistoryData) -> RouteHistoryDTO:
        """Convert RouteHistoryData to DTO."""
        return RouteHistoryDTO(
            id=data.id,
            route_id=data.route_id,
            deployment_id=data.deployment_id,
            category=data.category,
            phase=data.phase,
            from_status=data.from_status,
            to_status=data.to_status,
            from_sub_status=data.from_sub_status,
            to_sub_status=data.to_sub_status,
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
