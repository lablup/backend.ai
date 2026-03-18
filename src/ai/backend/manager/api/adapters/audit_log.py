"""Audit Log adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.audit_log.request import (
    AdminSearchAuditLogsInput,
    AuditLogOrder,
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
from ai.backend.manager.repositories.audit_log.options import AuditLogConditions, AuditLogOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 20


class AuditLogAdapter(BaseAdapter):
    """Adapter for audit log domain operations."""

    async def admin_search(self, input: AdminSearchAuditLogsInput) -> AdminSearchAuditLogsPayload:
        """Search audit logs with filters, ordering, and pagination."""
        querier = self._build_audit_log_querier(input)
        action_result = await self._processors.audit_log.search.wait_for_complete(
            SearchAuditLogsAction(querier=querier)
        )
        return AdminSearchAuditLogsPayload(
            items=[self._audit_log_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_audit_log_querier(self, input: AdminSearchAuditLogsInput) -> BatchQuerier:
        conditions: list[QueryCondition] = []
        if input.filter:
            f = input.filter
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
                if f.status.equals is not None:
                    conditions.append(AuditLogConditions.by_status_in([f.status.equals.value]))
                elif f.status.in_ is not None:
                    conditions.append(
                        AuditLogConditions.by_status_in([s.value for s in f.status.in_])
                    )
                elif f.status.not_in is not None:
                    conditions.append(
                        AuditLogConditions.by_status_not_in([s.value for s in f.status.not_in])
                    )
            if f.created_at_before is not None:
                conditions.append(AuditLogConditions.by_created_at_before(f.created_at_before))
            if f.created_at_after is not None:
                conditions.append(AuditLogConditions.by_created_at_after(f.created_at_after))
        orders: list[QueryOrder] = (
            self._convert_audit_log_orders(input.order) if input.order else []
        )
        orders.append(AuditLogOrders.created_at(ascending=False))
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    @staticmethod
    def _convert_audit_log_orders(orders: list[AuditLogOrder]) -> list[QueryOrder]:
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
    def _audit_log_data_to_dto(data: AuditLogData) -> AuditLogNode:
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
