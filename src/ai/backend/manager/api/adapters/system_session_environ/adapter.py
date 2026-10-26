"""System session environ domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.dto.manager.query import EnumFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    SystemSessionEnvironFilter,
    SystemSessionEnvironOrder,
    SystemSessionEnvironValueSourceFilter,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    AdminSearchSystemSessionEnvironsPayload,
    ListSystemSessionEnvironValueSourcesPayload,
    SystemSessionEnvironNode,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironOrderField,
    SystemSessionEnvironScopeInfo,
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.errors.system_session_environ import (
    UnknownSystemSessionEnvironValueSource,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)
from ai.backend.manager.models.system_session_environ.searchers import (
    SystemSessionEnvironSearcher,
)
from ai.backend.manager.services.system_session_environ.actions.bulk_get import (
    BulkGetSystemSessionEnvironsAction,
)
from ai.backend.manager.services.system_session_environ.actions.global_search import (
    GlobalSearchSystemSessionEnvironsAction,
)
from ai.backend.manager.services.system_session_environ.processors import (
    SystemSessionEnvironProcessors,
)

__all__ = ("SystemSessionEnvironAdapter",)

_SYSTEM_SESSION_ENVIRON_PAGINATION_SPEC = PaginationSpec(
    forward_order=SystemSessionEnvironSearchableFields.own.key.order.apply(ascending=True),
    cursor_column=SystemSessionEnvironRow.id,
)


class SystemSessionEnvironAdapter(BaseAdapter):
    """Adapter for the system session environ search and the reads by id."""

    _system_session_environ: SystemSessionEnvironProcessors

    def __init__(self, system_session_environ: SystemSessionEnvironProcessors) -> None:
        self._system_session_environ = system_session_environ

    async def global_search(
        self, input: AdminSearchSystemSessionEnvironsInput
    ) -> AdminSearchSystemSessionEnvironsPayload:
        """Search every system session environ row, at every scope (superadmin)."""
        searcher = self._build_searcher(
            SystemSessionEnvironSearcher,
            conditions=self._convert_filter(input.filter) if input.filter else [],
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_SYSTEM_SESSION_ENVIRON_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._system_session_environ.global_search.run(
            GlobalSearchSystemSessionEnvironsAction(
                searcher=GlobalSearcher(used_by=(), searcher=searcher)
            )
        )
        return AdminSearchSystemSessionEnvironsPayload(
            items=[self._data_to_node(environ) for environ in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def list_value_sources(self) -> ListSystemSessionEnvironValueSourcesPayload:
        """Every value source a system session environ row can carry."""
        return ListSystemSessionEnvironValueSourcesPayload(
            items=[value_source.value for value_source in SystemSessionEnvironValueSource]
        )

    async def bulk_get_ids(
        self, ids: Sequence[SystemSessionEnvironID]
    ) -> list[SystemSessionEnvironNode | Exception | None]:
        """Batch load system session environ rows by id for DataLoader use, one answer per id."""
        if not ids:
            return []
        result = await self._system_session_environ.bulk_get_ids.run(
            BulkGetSystemSessionEnvironsAction(ids=list(ids))
        )
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    def _convert_filter(self, filter: SystemSessionEnvironFilter) -> list[QueryCondition]:
        fields = SystemSessionEnvironSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_uuid_filter(filter.entity_id, fields.id.filter),
            *self.apply_string_filter(filter.key, fields.key.filter),
            *self.apply_enum_filter(
                self._value_source_filter(filter.value_source), fields.value_source.filter
            ),
            *self.apply_enum_filter(filter.scope_type, fields.scope_type.filter),
            *self.apply_uuid_filter(filter.scope_id, fields.scope_id.filter),
            *self.apply_bool_filter(filter.enabled, fields.enabled.filter),
        ]
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    or_conditions.append(combine_conditions_and(sub_conditions))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            for sub_filter in filter.NOT:
                sub_conditions = self._convert_filter(sub_filter)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

    def _value_source_filter(
        self, value_source_filter: SystemSessionEnvironValueSourceFilter | None
    ) -> EnumFilter[SystemSessionEnvironValueSource] | None:
        if value_source_filter is None:
            return None
        equals = value_source_filter.equals
        not_equals = value_source_filter.not_equals
        return EnumFilter[SystemSessionEnvironValueSource](
            equals=self._value_source_named(equals) if equals is not None else None,
            in_=[self._value_source_named(name) for name in value_source_filter.in_]
            if value_source_filter.in_ is not None
            else None,
            not_equals=self._value_source_named(not_equals) if not_equals is not None else None,
            not_in=[self._value_source_named(name) for name in value_source_filter.not_in]
            if value_source_filter.not_in is not None
            else None,
        )

    def _value_source_named(self, name: str) -> SystemSessionEnvironValueSource:
        try:
            return SystemSessionEnvironValueSource(name)
        except ValueError as e:
            raise UnknownSystemSessionEnvironValueSource(name) from e

    def _convert_orders(self, orders: list[SystemSessionEnvironOrder]) -> list[QueryOrder]:
        return [self._convert_order(order) for order in orders]

    def _convert_order(self, order: SystemSessionEnvironOrder) -> QueryOrder:
        fields = SystemSessionEnvironSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case SystemSessionEnvironOrderField.KEY:
                return fields.key.order.apply(ascending)
            case SystemSessionEnvironOrderField.VALUE_SOURCE:
                return fields.value_source.order.apply(ascending)
            case SystemSessionEnvironOrderField.SCOPE_TYPE:
                return fields.scope_type.order.apply(ascending)
            case SystemSessionEnvironOrderField.ENABLED:
                return fields.enabled.order.apply(ascending)
            case SystemSessionEnvironOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case SystemSessionEnvironOrderField.UPDATED_AT:
                return fields.updated_at.order.apply(ascending)
            case _:
                assert_never(order.field)

    @staticmethod
    def _data_to_node(environ: SystemSessionEnvironData) -> SystemSessionEnvironNode:
        return SystemSessionEnvironNode(
            entity_id=environ.id,
            key=environ.key,
            value_source=environ.value_source.value,
            scope=SystemSessionEnvironScopeInfo(
                scope_type=SystemSessionEnvironScopeType.of_owner(environ.scope_id),
                scope_id=SystemSessionEnvironScopeID(environ.scope_id),
            ),
            enabled=environ.enabled,
            created_at=environ.created_at,
            updated_at=environ.updated_at,
        )
