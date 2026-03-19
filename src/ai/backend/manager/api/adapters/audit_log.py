"""Audit Log adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.audit_log.request import (
    AdminSearchAuditLogsInput,
    AuditLogFilter,
    AuditLogOrder,
    AuditLogStatusFilter,
)
from ai.backend.common.dto.manager.v2.audit_log.response import (
    AdminSearchAuditLogsPayload,
    AuditLogNode,
)
from ai.backend.common.dto.manager.v2.audit_log.types import (
    AuditLogOrderField,
    AuditLogStatus,
    OrderDirection,
)
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.audit_log.options import AuditLogConditions, AuditLogOrders
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction

from .base import BaseAdapter
from .pagination import PaginationSpec

_AUDIT_LOG_PAGINATION_SPEC = PaginationSpec(
    forward_order=AuditLogOrders.created_at(ascending=False),
    backward_order=AuditLogOrders.created_at(ascending=True),
    forward_condition_factory=AuditLogConditions.by_cursor_forward,
    backward_condition_factory=AuditLogConditions.by_cursor_backward,
    tiebreaker_order=AuditLogRow.id.asc(),
)


class AuditLogAdapter(BaseAdapter):
    """Adapter for audit log domain operations."""

    async def admin_search(self, input: AdminSearchAuditLogsInput) -> AdminSearchAuditLogsPayload:
        """Search audit logs with filters, ordering, and pagination."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_AUDIT_LOG_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.audit_log.search.wait_for_complete(
            SearchAuditLogsAction(querier=querier)
        )
        return AdminSearchAuditLogsPayload(
            items=[self._data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_filter(self, f: AuditLogFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.entity_type is not None:
            condition = self.convert_string_filter(
                f.entity_type,
                contains_factory=AuditLogConditions.by_entity_type_contains,
                equals_factory=AuditLogConditions.by_entity_type_equals,
                starts_with_factory=AuditLogConditions.by_entity_type_starts_with,
                ends_with_factory=AuditLogConditions.by_entity_type_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        if f.operation is not None:
            condition = self.convert_string_filter(
                f.operation,
                contains_factory=AuditLogConditions.by_operation_contains,
                equals_factory=AuditLogConditions.by_operation_equals,
                starts_with_factory=AuditLogConditions.by_operation_starts_with,
                ends_with_factory=AuditLogConditions.by_operation_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        if f.triggered_by is not None:
            condition = self.convert_string_filter(
                f.triggered_by,
                contains_factory=AuditLogConditions.by_triggered_by_contains,
                equals_factory=AuditLogConditions.by_triggered_by_equals,
                starts_with_factory=AuditLogConditions.by_triggered_by_starts_with,
                ends_with_factory=AuditLogConditions.by_triggered_by_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        if f.status is not None:
            self._apply_status_filter(f.status, conditions)
        if f.created_at is not None:
            condition = f.created_at.build_query_condition(
                before_factory=AuditLogConditions.by_created_at_before,
                after_factory=AuditLogConditions.by_created_at_after,
            )
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub_filter in f.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in f.OR:
                or_conditions.extend(self._convert_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in f.NOT:
                not_conditions.extend(self._convert_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _apply_status_filter(s: AuditLogStatusFilter, conditions: list[QueryCondition]) -> None:
        if s.equals is not None:
            conditions.append(AuditLogConditions.by_status_in([s.equals.value]))
        elif s.in_ is not None:
            conditions.append(AuditLogConditions.by_status_in([v.value for v in s.in_]))
        elif s.not_in is not None:
            conditions.append(AuditLogConditions.by_status_not_in([v.value for v in s.not_in]))

    @staticmethod
    def _convert_orders(orders: list[AuditLogOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case AuditLogOrderField.CREATED_AT:
                    result.append(AuditLogOrders.created_at(ascending))
                case AuditLogOrderField.ENTITY_TYPE:
                    result.append(AuditLogOrders.entity_type(ascending))
                case AuditLogOrderField.OPERATION:
                    result.append(AuditLogOrders.operation(ascending))
                case AuditLogOrderField.STATUS:
                    result.append(AuditLogOrders.status(ascending))
        return result

    @staticmethod
    def _data_to_node(data: AuditLogData) -> AuditLogNode:
        return AuditLogNode(
            id=data.id,
            action_id=data.action_id,
            entity_type=data.entity_type,
            operation=data.operation,
            entity_id=data.entity_id,
            created_at=data.created_at,
            request_id=data.request_id,
            triggered_by=data.triggered_by,
            description=data.description,
            duration=str(data.duration) if data.duration is not None else None,
            status=AuditLogStatus(data.status.value),
        )
