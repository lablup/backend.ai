"""System session environ domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.dto.manager.query import EnumFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    CreateSystemSessionEnvironInput,
    SystemSessionEnvironFilter,
    SystemSessionEnvironOrder,
    SystemSessionEnvironValueSourceFilter,
    UpdateSystemSessionEnvironInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    AdminSearchSystemSessionEnvironsPayload,
    CreateSystemSessionEnvironPayload,
    DeleteSystemSessionEnvironPayload,
    ListSystemSessionEnvironValueSourcesPayload,
    PurgeSystemSessionEnvironPayload,
    RestoreSystemSessionEnvironPayload,
    SystemSessionEnvironNode,
    UpdateSystemSessionEnvironPayload,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironOrderField,
    SystemSessionEnvironScopeInfo,
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.permission.global_entity import global_entity_id
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
from ai.backend.manager.models.specs.soft_delete import RestoreUpdater, SoftDeleteUpdater
from ai.backend.manager.models.system_session_environ.creators import (
    SystemSessionEnvironCreator,
)
from ai.backend.manager.models.system_session_environ.purgers import (
    SystemSessionEnvironPurger,
)
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)
from ai.backend.manager.models.system_session_environ.searchers import (
    SystemSessionEnvironSearcher,
)
from ai.backend.manager.models.system_session_environ.updaters import (
    SystemSessionEnvironUpdater,
)
from ai.backend.manager.services.system_session_environ.actions.bulk_get import (
    BulkGetSystemSessionEnvironsAction,
)
from ai.backend.manager.services.system_session_environ.actions.create import (
    CreateSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.actions.delete import (
    DeleteSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.actions.global_search import (
    GlobalSearchSystemSessionEnvironsAction,
)
from ai.backend.manager.services.system_session_environ.actions.public_list_value_sources import (
    PublicListSystemSessionEnvironValueSourcesAction,
)
from ai.backend.manager.services.system_session_environ.actions.purge import (
    PurgeSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.actions.restore import (
    RestoreSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.actions.update import (
    UpdateSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.processors import (
    SystemSessionEnvironProcessors,
)
from ai.backend.manager.types import OptionalState

__all__ = ("SystemSessionEnvironAdapter",)

_SYSTEM_SESSION_ENVIRON_PAGINATION_SPEC = PaginationSpec(
    forward_order=SystemSessionEnvironSearchableFields.own.key.order.apply(ascending=True),
    cursor_column=SystemSessionEnvironRow.id,
)


class SystemSessionEnvironAdapter(BaseAdapter):
    _system_session_environ: SystemSessionEnvironProcessors

    def __init__(self, system_session_environ: SystemSessionEnvironProcessors) -> None:
        self._system_session_environ = system_session_environ

    async def global_search(
        self, input: AdminSearchSystemSessionEnvironsInput
    ) -> AdminSearchSystemSessionEnvironsPayload:
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

    async def public_list_value_sources(self) -> ListSystemSessionEnvironValueSourcesPayload:
        result = await self._system_session_environ.public_list_value_sources.run(
            PublicListSystemSessionEnvironValueSourcesAction()
        )
        return ListSystemSessionEnvironValueSourcesPayload(
            items=[value_source.value for value_source in result.value_sources]
        )

    async def create(
        self, input: CreateSystemSessionEnvironInput
    ) -> CreateSystemSessionEnvironPayload:
        """Bind a value source to an environment variable name at one scope."""
        result = await self._system_session_environ.create.run(
            CreateSystemSessionEnvironAction(
                creator=SystemSessionEnvironCreator(
                    owner=self._owner_of(input.scope_type, input.scope_id),
                    value_source=self._value_source_named(input.value_source),
                    key=input.key,
                )
            )
        )
        return CreateSystemSessionEnvironPayload(
            system_session_environ=self._data_to_node(result.data)
        )

    async def update(
        self, environ_id: SystemSessionEnvironID, input: UpdateSystemSessionEnvironInput
    ) -> UpdateSystemSessionEnvironPayload:
        """Change a system session environ row's key."""
        result = await self._system_session_environ.update.run(
            UpdateSystemSessionEnvironAction(
                updater=SystemSessionEnvironUpdater(
                    environ_id=environ_id,
                    key=OptionalState.from_unset(input.key),
                )
            )
        )
        return UpdateSystemSessionEnvironPayload(
            system_session_environ=self._data_to_node(result.data)
        )

    async def delete(self, environ_id: SystemSessionEnvironID) -> DeleteSystemSessionEnvironPayload:
        """Soft-delete a system session environ row."""
        result = await self._system_session_environ.delete.run(
            DeleteSystemSessionEnvironAction(
                updater=SoftDeleteUpdater(
                    target_row=SystemSessionEnvironRow,
                    target_column=SystemSessionEnvironRow.id,
                    target_id=environ_id,
                    converter=SystemSessionEnvironSearchableFields.own,
                )
            )
        )
        return DeleteSystemSessionEnvironPayload(
            system_session_environ=self._data_to_node(result.data)
        )

    async def restore(
        self, environ_id: SystemSessionEnvironID
    ) -> RestoreSystemSessionEnvironPayload:
        """Restore a soft-deleted system session environ row."""
        result = await self._system_session_environ.restore.run(
            RestoreSystemSessionEnvironAction(
                updater=RestoreUpdater(
                    target_row=SystemSessionEnvironRow,
                    target_column=SystemSessionEnvironRow.id,
                    target_id=environ_id,
                    converter=SystemSessionEnvironSearchableFields.own,
                )
            )
        )
        return RestoreSystemSessionEnvironPayload(
            system_session_environ=self._data_to_node(result.data)
        )

    async def purge(self, environ_id: SystemSessionEnvironID) -> PurgeSystemSessionEnvironPayload:
        """Remove a system session environ row for good, soft-deleted or not."""
        result = await self._system_session_environ.purge.run(
            PurgeSystemSessionEnvironAction(
                purger=SystemSessionEnvironPurger(environ_id=environ_id)
            )
        )
        return PurgeSystemSessionEnvironPayload(entity_id=result.data.id)

    async def bulk_get_ids(
        self, ids: Sequence[SystemSessionEnvironID]
    ) -> list[SystemSessionEnvironNode | Exception | None]:
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
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.updated_at, fields.updated_at.filter),
            *self.apply_nullable_datetime_filter(filter.deleted_at, fields.deleted_at.filter),
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

    def _owner_of(
        self,
        scope_type: SystemSessionEnvironScopeType,
        scope_id: SystemSessionEnvironScopeID | None,
    ) -> EntityIdentifier:
        match scope_type:
            case SystemSessionEnvironScopeType.PUBLIC:
                return global_entity_id(GlobalEntityName.PUBLIC)
            case SystemSessionEnvironScopeType.DOMAIN | SystemSessionEnvironScopeType.PROJECT:
                if scope_id is None:
                    raise UnreachableError(f"A {scope_type} system session environ has no scope id")
                return scope_type.to_owner(scope_id)

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
            case SystemSessionEnvironOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case SystemSessionEnvironOrderField.UPDATED_AT:
                return fields.updated_at.order.apply(ascending)
            case SystemSessionEnvironOrderField.DELETED_AT:
                return fields.deleted_at.order.apply(ascending)
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
            created_at=environ.created_at,
            updated_at=environ.updated_at,
            deleted_at=environ.deleted_at,
        )
