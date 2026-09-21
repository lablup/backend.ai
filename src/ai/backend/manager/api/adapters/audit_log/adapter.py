"""Audit Log adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import assert_never

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.audit_log.request import (
    AdminSearchAuditLogsInput,
    AuditLogFilter,
    AuditLogOrder,
    AuditLogStatusFilter,
    ScopedSearchAuditLogsInput,
)
from ai.backend.common.dto.manager.v2.audit_log.response import (
    AuditLogNode,
    SearchAuditLogsPayload,
)
from ai.backend.common.dto.manager.v2.audit_log.types import (
    AuditLogOrderField,
    AuditLogStatus,
    OrderDirection,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.models.audit_log.scopes import (
    AuditLogTarget,
    EntityAuditLogTarget,
    ScopeAuditLogTarget,
    TriggeredByAuditLogTarget,
)
from ai.backend.manager.models.audit_log.searchable_fields import AuditLogSearchableFields
from ai.backend.manager.models.audit_log.searchers import AuditLogSearcher
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.audit_log.actions.bulk_get import BulkGetAuditLogsAction
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    ScopedSearchAuditLogsAction,
)
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors

_AUDIT_LOG_PAGINATION_SPEC = PaginationSpec(
    forward_order=AuditLogSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=AuditLogRow.id,
)


class AuditLogAdapter(BaseAdapter):
    """Adapter for audit log domain operations."""

    _audit_log: AuditLogProcessors

    def __init__(self, audit_log: AuditLogProcessors) -> None:
        self._audit_log = audit_log

    async def batch_load_by_ids(
        self, ids: Sequence[AuditLogID]
    ) -> list[AuditLogNode | Exception | None]:
        """Batch load audit logs for DataLoader use, checked per entity each is about."""
        if not ids:
            return []
        audit_log_ids = [AuditLogID(audit_log_id) for audit_log_id in ids]
        return await self.batch_load_fields(
            self._audit_log.bulk_get,
            BulkGetAuditLogsAction(ids=audit_log_ids),
            audit_log_ids,
            self._data_to_node,
        )

    async def admin_search(self, input: AdminSearchAuditLogsInput) -> SearchAuditLogsPayload:
        """Search audit logs with filters, ordering, and pagination."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            AuditLogSearcher,
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
        action_result = await self._audit_log.global_search.run(
            SearchAuditLogsAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return SearchAuditLogsPayload(
            items=[self._data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def scoped_search(self, input: ScopedSearchAuditLogsInput) -> SearchAuditLogsPayload:
        """Scoped audit-log search: caller passes a list of scope items; results
        are the OR-union of matching rows, restricted to items the caller is
        RBAC-authorized for."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            AuditLogSearcher,
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
        action_result = await self._audit_log.scoped_search.run(
            ScopedSearchAuditLogsAction(targets=self._scope_targets(input), searcher=searcher)
        )
        return SearchAuditLogsPayload(
            items=[self._data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    @staticmethod
    def _scope_targets(input: ScopedSearchAuditLogsInput) -> list[AuditLogTarget]:
        """The scopes the request names; an entity id that is not one is refused here.

        A scope is an entity — a session, a deployment, a user — so its id has to be one.
        """
        targets: list[AuditLogTarget] = []
        for entity_scope in input.scope.entity or []:
            try:
                entity_id = uuid.UUID(entity_scope.entity_id)
            except ValueError as e:
                raise InvalidAPIParameters(
                    f"Audit log scope id {entity_scope.entity_id!r} is not an entity id"
                ) from e
            owner = RuntimeEntityID(EntityType(entity_scope.entity_type), entity_id)
            # An entity's history is both halves: what was done to it, and what was done
            # in it. The request names the entity once and the action ORs the two.
            targets.append(EntityAuditLogTarget(owner=owner))
            targets.append(ScopeAuditLogTarget(owner=owner))
        for user_scope in input.scope.triggered_user or []:
            targets.append(TriggeredByAuditLogTarget(user_id=UserID(user_scope.value)))
        return targets

    def _convert_filter(self, f: AuditLogFilter) -> list[QueryCondition]:
        fields = AuditLogSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_string_filter(f.entity_type, fields.entity_type.filter),
            *self.apply_string_filter(f.entity_id, fields.target_entity_id.filter),
            *self.apply_string_filter(f.operation, fields.operation.filter),
            *self.apply_string_filter(f.triggered_by, fields.triggered_by.filter),
            *self.apply_uuid_filter(f.acted_as, fields.acted_as.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
        ]
        if f.status is not None:
            self._apply_status_filter(f.status, conditions)
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
        status = AuditLogSearchableFields.own.status.filter
        if s.equals is not None:
            conditions.append(status.equals(status.to_value(s.equals)))
        if s.in_ is not None:
            conditions.append(status.in_([status.to_value(value) for value in s.in_]))
        if s.not_equals is not None:
            conditions.append(status.not_equals(status.to_value(s.not_equals)))
        if s.not_in is not None:
            conditions.append(status.not_in([status.to_value(value) for value in s.not_in]))

    @staticmethod
    def _convert_orders(orders: list[AuditLogOrder]) -> list[QueryOrder]:
        fields = AuditLogSearchableFields.own
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case AuditLogOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case AuditLogOrderField.ENTITY_TYPE:
                    result.append(fields.entity_type.order.apply(ascending))
                case AuditLogOrderField.OPERATION:
                    result.append(fields.operation.order.apply(ascending))
                case AuditLogOrderField.STATUS:
                    result.append(fields.status.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return result

    @staticmethod
    def _data_to_node(data: AuditLogData) -> AuditLogNode:
        return AuditLogNode(
            id=data.id,
            field_id=data.id,
            action_id=data.action_id,
            entity_type=data.entity_type,
            operation=data.operation,
            entity_id=data.target_entity_id,
            created_at=data.created_at,
            request_id=data.request_id,
            triggered_by=data.triggered_by,
            acted_as=data.acted_as,
            description=data.description,
            duration=str(data.duration) if data.duration is not None else None,
            client_ip=data.client_ip,
            status=AuditLogStatus(data.status.value),
        )
