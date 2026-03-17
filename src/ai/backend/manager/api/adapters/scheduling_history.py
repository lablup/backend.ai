"""Scheduling history adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    RouteHistoryFilter,
    RouteHistoryOrder,
    SessionHistoryFilter,
    SessionHistoryOrder,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    AdminSearchDeploymentHistoriesPayload,
    AdminSearchRouteHistoriesPayload,
    AdminSearchSessionHistoriesPayload,
    DeploymentHistoryNode,
    RouteHistoryNode,
    SessionHistoryNode,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import SubStepResultInfo
from ai.backend.manager.data.deployment.types import DeploymentHistoryData, RouteHistoryData
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SubStepResult,
)
from ai.backend.manager.models.scheduling_history.conditions import (
    DeploymentHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)
from ai.backend.manager.models.scheduling_history.orders import (
    DEPLOYMENT_DEFAULT_FORWARD_ORDER,
    DEPLOYMENT_TIEBREAKER_ORDER,
    ROUTE_DEFAULT_FORWARD_ORDER,
    ROUTE_TIEBREAKER_ORDER,
    SESSION_DEFAULT_FORWARD_ORDER,
    SESSION_TIEBREAKER_ORDER,
    resolve_deployment_order,
    resolve_route_order,
    resolve_session_order,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.scheduling_history.types import (
    DeploymentHistorySearchScope,
    RouteHistorySearchScope,
    SessionSchedulingHistorySearchScope,
)
from ai.backend.manager.services.scheduling_history.actions.search_deployment_history import (
    SearchDeploymentHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_deployment_scoped_history import (
    SearchDeploymentScopedHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_route_history import (
    SearchRouteHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_route_scoped_history import (
    SearchRouteScopedHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_session_history import (
    SearchSessionHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_session_scoped_history import (
    SearchSessionScopedHistoryAction,
)

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 50


class SchedulingHistoryAdapter(BaseAdapter):
    """Adapter for scheduling history domain operations."""

    # ========== Session History ==========

    async def admin_search_session_history(
        self,
        input: AdminSearchSessionHistoriesInput,
    ) -> AdminSearchSessionHistoriesPayload:
        """Search session scheduling histories (admin, no scope)."""
        querier = self._build_session_querier(input)
        action_result = (
            await self._processors.scheduling_history.search_session_history.wait_for_complete(
                SearchSessionHistoryAction(querier=querier)
            )
        )
        return AdminSearchSessionHistoriesPayload(
            items=[self._session_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def session_scoped_search(
        self,
        session_id: UUID,
        input: AdminSearchSessionHistoriesInput,
    ) -> AdminSearchSessionHistoriesPayload:
        """Search session scheduling histories scoped to a session."""
        scope = SessionSchedulingHistorySearchScope(session_id=session_id)
        querier = self._build_session_querier(input)
        action_result = await self._processors.scheduling_history.search_session_scoped_history.wait_for_complete(
            SearchSessionScopedHistoryAction(scope=scope, querier=querier)
        )
        return AdminSearchSessionHistoriesPayload(
            items=[self._session_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_session_querier(self, input: AdminSearchSessionHistoriesInput) -> BatchQuerier:
        conditions = self._convert_session_filter(input.filter) if input.filter else []
        orders = (
            self._convert_session_orders(input.order)
            if input.order
            else [SESSION_DEFAULT_FORWARD_ORDER]
        )
        orders.append(SESSION_TIEBREAKER_ORDER)
        pagination = self._build_pagination(input.limit, input.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_session_filter(self, filter: SessionHistoryFilter) -> list[QueryCondition]:
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
        if filter.from_status is not None and filter.from_status:
            conditions.append(
                SessionSchedulingHistoryConditions.by_from_statuses(filter.from_status)
            )
        if filter.to_status is not None and filter.to_status:
            conditions.append(SessionSchedulingHistoryConditions.by_to_statuses(filter.to_status))
        if filter.result is not None and filter.result:
            conditions.append(
                SessionSchedulingHistoryConditions.by_results([
                    SchedulingResult(r.value) for r in filter.result
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

    @staticmethod
    def _convert_session_orders(order: list[SessionHistoryOrder]) -> list[QueryOrder]:
        return [resolve_session_order(o.field, o.direction) for o in order]

    # ========== Deployment History ==========

    async def admin_search_deployment_history(
        self,
        input: AdminSearchDeploymentHistoriesInput,
    ) -> AdminSearchDeploymentHistoriesPayload:
        """Search deployment histories (admin, no scope)."""
        querier = self._build_deployment_querier(input)
        action_result = (
            await self._processors.scheduling_history.search_deployment_history.wait_for_complete(
                SearchDeploymentHistoryAction(querier=querier)
            )
        )
        return AdminSearchDeploymentHistoriesPayload(
            items=[self._deployment_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def deployment_scoped_search(
        self,
        deployment_id: UUID,
        input: AdminSearchDeploymentHistoriesInput,
    ) -> AdminSearchDeploymentHistoriesPayload:
        """Search deployment histories scoped to a deployment."""
        scope = DeploymentHistorySearchScope(deployment_id=deployment_id)
        querier = self._build_deployment_querier(input)
        action_result = await self._processors.scheduling_history.search_deployment_scoped_history.wait_for_complete(
            SearchDeploymentScopedHistoryAction(scope=scope, querier=querier)
        )
        return AdminSearchDeploymentHistoriesPayload(
            items=[self._deployment_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_deployment_querier(self, input: AdminSearchDeploymentHistoriesInput) -> BatchQuerier:
        conditions = self._convert_deployment_filter(input.filter) if input.filter else []
        orders = (
            self._convert_deployment_orders(input.order)
            if input.order
            else [DEPLOYMENT_DEFAULT_FORWARD_ORDER]
        )
        orders.append(DEPLOYMENT_TIEBREAKER_ORDER)
        pagination = self._build_pagination(input.limit, input.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_deployment_filter(self, filter: DeploymentHistoryFilter) -> list[QueryCondition]:
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
        if filter.from_status is not None and filter.from_status:
            conditions.append(DeploymentHistoryConditions.by_from_statuses(filter.from_status))
        if filter.to_status is not None and filter.to_status:
            conditions.append(DeploymentHistoryConditions.by_to_statuses(filter.to_status))
        if filter.result is not None and filter.result:
            conditions.append(
                DeploymentHistoryConditions.by_results([
                    SchedulingResult(r.value) for r in filter.result
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

    @staticmethod
    def _convert_deployment_orders(order: list[DeploymentHistoryOrder]) -> list[QueryOrder]:
        return [resolve_deployment_order(o.field, o.direction) for o in order]

    # ========== Route History ==========

    async def admin_search_route_history(
        self,
        input: AdminSearchRouteHistoriesInput,
    ) -> AdminSearchRouteHistoriesPayload:
        """Search route histories (admin, no scope)."""
        querier = self._build_route_querier(input)
        action_result = (
            await self._processors.scheduling_history.search_route_history.wait_for_complete(
                SearchRouteHistoryAction(querier=querier)
            )
        )
        return AdminSearchRouteHistoriesPayload(
            items=[self._route_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def route_scoped_search(
        self,
        route_id: UUID,
        input: AdminSearchRouteHistoriesInput,
    ) -> AdminSearchRouteHistoriesPayload:
        """Search route histories scoped to a route."""
        scope = RouteHistorySearchScope(route_id=route_id)
        querier = self._build_route_querier(input)
        action_result = (
            await self._processors.scheduling_history.search_route_scoped_history.wait_for_complete(
                SearchRouteScopedHistoryAction(scope=scope, querier=querier)
            )
        )
        return AdminSearchRouteHistoriesPayload(
            items=[self._route_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_route_querier(self, input: AdminSearchRouteHistoriesInput) -> BatchQuerier:
        conditions = self._convert_route_filter(input.filter) if input.filter else []
        orders = (
            self._convert_route_orders(input.order)
            if input.order
            else [ROUTE_DEFAULT_FORWARD_ORDER]
        )
        orders.append(ROUTE_TIEBREAKER_ORDER)
        pagination = self._build_pagination(input.limit, input.offset)
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_route_filter(self, filter: RouteHistoryFilter) -> list[QueryCondition]:
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
        if filter.from_status is not None and filter.from_status:
            conditions.append(RouteHistoryConditions.by_from_statuses(filter.from_status))
        if filter.to_status is not None and filter.to_status:
            conditions.append(RouteHistoryConditions.by_to_statuses(filter.to_status))
        if filter.result is not None and filter.result:
            conditions.append(
                RouteHistoryConditions.by_results([
                    SchedulingResult(r.value) for r in filter.result
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

    @staticmethod
    def _convert_route_orders(order: list[RouteHistoryOrder]) -> list[QueryOrder]:
        return [resolve_route_order(o.field, o.direction) for o in order]

    # ========== Pagination ==========

    @staticmethod
    def _build_pagination(limit: int | None, offset: int | None) -> OffsetPagination:
        return OffsetPagination(
            limit=limit if limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=offset if offset is not None else 0,
        )

    # ========== Data → DTO Conversion ==========

    @staticmethod
    def _convert_sub_step(step: SubStepResult) -> SubStepResultInfo:
        return SubStepResultInfo(
            step=step.step,
            result=step.result.value,
            error_code=step.error_code,
            message=step.message,
            started_at=step.started_at,
            ended_at=step.ended_at,
        )

    @staticmethod
    def _session_data_to_dto(data: SessionSchedulingHistoryData) -> SessionHistoryNode:
        return SessionHistoryNode(
            id=data.id,
            session_id=data.session_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=data.result.value,
            error_code=data.error_code,
            message=data.message,
            sub_steps=[
                SubStepResultInfo(
                    step=s.step,
                    result=s.result.value,
                    error_code=s.error_code,
                    message=s.message,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                )
                for s in data.sub_steps
            ],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _deployment_data_to_dto(data: DeploymentHistoryData) -> DeploymentHistoryNode:
        return DeploymentHistoryNode(
            id=data.id,
            deployment_id=data.deployment_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=data.result.value,
            error_code=data.error_code,
            message=data.message,
            sub_steps=[
                SubStepResultInfo(
                    step=s.step,
                    result=s.result.value,
                    error_code=s.error_code,
                    message=s.message,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                )
                for s in data.sub_steps
            ],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _route_data_to_dto(data: RouteHistoryData) -> RouteHistoryNode:
        return RouteHistoryNode(
            id=data.id,
            route_id=data.route_id,
            deployment_id=data.deployment_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=data.result.value,
            error_code=data.error_code,
            message=data.message,
            sub_steps=[
                SubStepResultInfo(
                    step=s.step,
                    result=s.result.value,
                    error_code=s.error_code,
                    message=s.message,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                )
                for s in data.sub_steps
            ],
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
