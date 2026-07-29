"""Idle checker assignment adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from functools import lru_cache

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    CreateIdleCheckerAssignmentInput,
    IdleCheckerAssignmentFilter,
    IdleCheckerAssignmentOrder,
    PurgeIdleCheckerAssignmentInput,
    ScopedSearchIdleCheckerAssignmentsInput,
    SearchIdleCheckerAssignmentsInput,
    UpdateIdleCheckerAssignmentInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    CreateIdleCheckerAssignmentPayload,
    IdleCheckerAssignmentNode,
    PurgeIdleCheckerAssignmentPayload,
    SearchIdleCheckerAssignmentPayload,
    UpdateIdleCheckerAssignmentPayload,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import (
    IdleCheckerAssignmentOrderField,
    IdleCheckerScopeTypeDTO,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.errors.idle_checker import InvalidIdleCheckerAssignmentScopeId
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerAssignmentConditions
from ai.backend.manager.models.idle_checker.orders import IdleCheckerAssignmentOrders
from ai.backend.manager.repositories.base import (
    Updater,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerAssignmentCreatorSpec
from ai.backend.manager.repositories.idle_checker.purgers import IdleCheckerAssignmentPurgerSpec
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerAssignmentUpdaterSpec
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.create import (
    CreateIdleCheckerAssignmentAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.purge import (
    PurgeIdleCheckerAssignmentAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    IdleCheckerAssignmentScopeTarget,
    ScopedSearchIdleCheckerAssignmentsAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.update import (
    UpdateIdleCheckerAssignmentAction,
)
from ai.backend.manager.types import OptionalState


@lru_cache(maxsize=1)
def _get_idle_checker_assignment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=IdleCheckerAssignmentOrders.created_at(ascending=False),
        backward_order=IdleCheckerAssignmentOrders.created_at(ascending=True),
        forward_condition_factory=IdleCheckerAssignmentConditions.by_cursor_forward,
        backward_condition_factory=IdleCheckerAssignmentConditions.by_cursor_backward,
        tiebreaker_order=IdleCheckerAssignmentOrders.id(ascending=True),
    )


class IdleCheckerAssignmentAdapter(BaseAdapter):
    """Adapter for idle checker assignment domain operations."""

    @staticmethod
    def _parse_scope_id(scope_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(scope_id)
        except ValueError as e:
            raise InvalidIdleCheckerAssignmentScopeId(scope_id) from e

    async def admin_create(
        self, input: CreateIdleCheckerAssignmentInput
    ) -> CreateIdleCheckerAssignmentPayload:
        spec = IdleCheckerAssignmentCreatorSpec(
            scope_type=ScopeType(input.scope.scope_type.value),
            scope_id=self._parse_scope_id(input.scope.scope_id),
            idle_checker_id=input.idle_checker_id,
            enabled=input.enabled,
        )
        action_result = await self._processors.idle_checker_assignment.create.wait_for_complete(
            CreateIdleCheckerAssignmentAction(creator_spec=spec)
        )
        return CreateIdleCheckerAssignmentPayload(
            idle_checker_assignment=self._data_to_node(action_result.data)
        )

    async def update(
        self, input: UpdateIdleCheckerAssignmentInput
    ) -> UpdateIdleCheckerAssignmentPayload:
        updater = Updater(
            spec=IdleCheckerAssignmentUpdaterSpec(
                enabled=OptionalState[bool].update(input.enabled),
            ),
            pk_value=input.id,
        )
        action_result = await self._processors.idle_checker_assignment.update.wait_for_complete(
            UpdateIdleCheckerAssignmentAction(updater=updater)
        )
        return UpdateIdleCheckerAssignmentPayload(
            idle_checker_assignment=self._data_to_node(action_result.data)
        )

    async def purge(
        self, input: PurgeIdleCheckerAssignmentInput
    ) -> PurgeIdleCheckerAssignmentPayload:
        purger = RBACEntityPurger(spec=IdleCheckerAssignmentPurgerSpec(assignment_id=input.id))
        action_result = await self._processors.idle_checker_assignment.purge.wait_for_complete(
            PurgeIdleCheckerAssignmentAction(purger=purger)
        )
        return PurgeIdleCheckerAssignmentPayload(id=action_result.data.id)

    async def admin_search(
        self, input: SearchIdleCheckerAssignmentsInput
    ) -> SearchIdleCheckerAssignmentPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_idle_checker_assignment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = (
            await self._processors.idle_checker_assignment.admin_search.wait_for_complete(
                AdminSearchIdleCheckerAssignmentsAction(querier=querier)
            )
        )
        return SearchIdleCheckerAssignmentPayload(
            items=[self._data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def scoped_search(
        self, input: ScopedSearchIdleCheckerAssignmentsInput
    ) -> SearchIdleCheckerAssignmentPayload:
        """Scoped assignment search: scope items are OR'd, and each item is
        RBAC-validated against the caller before the query runs."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_idle_checker_assignment_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        targets: list[SearchableActionTarget] = []
        for ref in input.scope.items:
            targets.append(
                IdleCheckerAssignmentScopeTarget(
                    scope_type=ScopeType(ref.scope_type.value),
                    scope_id=self._parse_scope_id(ref.scope_id),
                )
            )
        action_result = (
            await self._processors.idle_checker_assignment.scoped_search.wait_for_complete(
                ScopedSearchIdleCheckerAssignmentsAction(items=targets, querier=querier)
            )
        )
        return SearchIdleCheckerAssignmentPayload(
            items=[self._data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_filter(self, f: IdleCheckerAssignmentFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.scope_type is not None:
            if f.scope_type.equals is not None:
                conditions.append(
                    IdleCheckerAssignmentConditions.by_scope_type_equals(
                        ScopeType(f.scope_type.equals.value)
                    )
                )
            if f.scope_type.in_ is not None:
                scope_types: list[ScopeType] = []
                for scope_type_dto in f.scope_type.in_:
                    scope_types.append(ScopeType(scope_type_dto.value))
                conditions.append(IdleCheckerAssignmentConditions.by_scope_type_in(scope_types))
        if f.scope_id is not None:
            condition = self.convert_uuid_filter(
                f.scope_id,
                equals_factory=IdleCheckerAssignmentConditions.by_scope_id_equals,
                in_factory=IdleCheckerAssignmentConditions.by_scope_id_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.idle_checker_id is not None:
            condition = self.convert_uuid_filter(
                f.idle_checker_id,
                equals_factory=IdleCheckerAssignmentConditions.by_idle_checker_id_equals,
                in_factory=IdleCheckerAssignmentConditions.by_idle_checker_id_in,
            )
            if condition is not None:
                conditions.append(condition)
        if f.enabled is not None:
            conditions.append(IdleCheckerAssignmentConditions.by_enabled_equals(f.enabled))
        if f.created_at is not None:
            condition = f.created_at.build_query_condition(
                before_factory=IdleCheckerAssignmentConditions.by_created_at_before,
                after_factory=IdleCheckerAssignmentConditions.by_created_at_after,
                equals_factory=IdleCheckerAssignmentConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if f.updated_at is not None:
            condition = f.updated_at.build_query_condition(
                before_factory=IdleCheckerAssignmentConditions.by_updated_at_before,
                after_factory=IdleCheckerAssignmentConditions.by_updated_at_after,
                equals_factory=IdleCheckerAssignmentConditions.by_updated_at_equals,
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
    def _convert_orders(orders: list[IdleCheckerAssignmentOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case IdleCheckerAssignmentOrderField.SCOPE_TYPE:
                    result.append(IdleCheckerAssignmentOrders.scope_type(ascending))
                case IdleCheckerAssignmentOrderField.ENABLED:
                    result.append(IdleCheckerAssignmentOrders.enabled(ascending))
                case IdleCheckerAssignmentOrderField.CREATED_AT:
                    result.append(IdleCheckerAssignmentOrders.created_at(ascending))
                case IdleCheckerAssignmentOrderField.UPDATED_AT:
                    result.append(IdleCheckerAssignmentOrders.updated_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: IdleCheckerAssignmentData) -> IdleCheckerAssignmentNode:
        return IdleCheckerAssignmentNode(
            id=IdleCheckerAssignmentID(data.id),
            scope_type=IdleCheckerScopeTypeDTO(data.scope_type.value),
            scope_id=str(data.scope_id),
            idle_checker_id=data.idle_checker_id,
            enabled=data.enabled,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
