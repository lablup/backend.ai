"""Idle checker assignment adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import assert_never

from ai.backend.common.data.entity.idle_checker import (
    IdleCheckerAssignmentID,
    IdleCheckerID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, RuntimeEntityID
from ai.backend.common.data.filter_specs import StringInMatchSpec, StringMatchSpec
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
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerAssignmentAlreadyExists,
    IdleCheckerAssignmentNotFound,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.idle_checker.creators import IdleCheckerAssignmentCreator
from ai.backend.manager.models.idle_checker.purgers import IdleCheckerAssignmentPurger
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow
from ai.backend.manager.models.idle_checker.searchable_fields import (
    IdleCheckerAssignmentSearchableFields,
)
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerAssignmentSearcher
from ai.backend.manager.models.idle_checker.updaters import (
    IdleCheckerAssignmentDisabler,
    IdleCheckerAssignmentEnabler,
)
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.lookup import (
    LookupIdleCheckerAssignmentAction,
    LookupIdleCheckerAssignmentByPairAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
)
from ai.backend.manager.services.idle_checker_assignment.processors import (
    IdleCheckerAssignmentProcessors,
)
from ai.backend.manager.services.rbac.actions.relation.base import RelationPair
from ai.backend.manager.services.rbac.actions.relation.create import CreateRelationAction
from ai.backend.manager.services.rbac.actions.relation.purge import PurgeRelationAction
from ai.backend.manager.services.rbac.actions.relation.switch import (
    DeleteRelationAction,
    RestoreRelationAction,
)
from ai.backend.manager.services.rbac.processors import RbacProcessors


@lru_cache(maxsize=1)
def _get_idle_checker_assignment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=IdleCheckerAssignmentSearchableFields.own.created_at.order.apply(
            ascending=False
        ),
        cursor_column=IdleCheckerBindingRow.id,
    )


class IdleCheckerAssignmentAdapter(BaseAdapter):
    """Adapter for idle checker assignment domain operations."""

    _idle_checker_assignment: IdleCheckerAssignmentProcessors
    _rbac: RbacProcessors

    def __init__(
        self,
        idle_checker_assignment: IdleCheckerAssignmentProcessors,
        rbac: RbacProcessors,
    ) -> None:
        self._idle_checker_assignment = idle_checker_assignment
        self._rbac = rbac

    async def admin_create(
        self, input: CreateIdleCheckerAssignmentInput
    ) -> CreateIdleCheckerAssignmentPayload:
        scope = self._scope_entity(input.scope.scope_type, input.scope.scope_id)
        result = await self._rbac.create_relation.run(
            CreateRelationAction(
                pairs=[RelationPair(scope=scope, target=input.idle_checker_id)],
                creator=IdleCheckerAssignmentCreator(enabled=input.enabled),
            )
        )
        if not all(link.linked for link in result.results):
            raise IdleCheckerAssignmentAlreadyExists(
                f"{scope.entity_type()}:{scope} -> {input.idle_checker_id}"
            )
        return CreateIdleCheckerAssignmentPayload(
            idle_checker_assignment=self._data_to_node(
                await self._read_by_pair(scope, input.idle_checker_id)
            )
        )

    async def update(
        self, input: UpdateIdleCheckerAssignmentInput
    ) -> UpdateIdleCheckerAssignmentPayload:
        """Switch the binding the id names on or off."""
        current = await self._resolve(input.id)
        pairs = [RelationPair(scope=current.scope_entity(), target=current.idle_checker_id)]
        if input.enabled:
            await self._rbac.restore_relation.run(
                RestoreRelationAction(pairs=pairs, updater=IdleCheckerAssignmentEnabler())
            )
        else:
            await self._rbac.delete_relation.run(
                DeleteRelationAction(pairs=pairs, updater=IdleCheckerAssignmentDisabler())
            )
        return UpdateIdleCheckerAssignmentPayload(
            idle_checker_assignment=self._data_to_node(
                await self._read_by_pair(current.scope_entity(), current.idle_checker_id)
            )
        )

    async def purge(
        self, input: PurgeIdleCheckerAssignmentInput
    ) -> PurgeIdleCheckerAssignmentPayload:
        current = await self._resolve(input.id)
        result = await self._rbac.purge_relation.run(
            PurgeRelationAction(
                pairs=[RelationPair(scope=current.scope_entity(), target=current.idle_checker_id)],
                purger=IdleCheckerAssignmentPurger(),
            )
        )
        if not any(unlink.unlinked for unlink in result.results):
            raise IdleCheckerAssignmentNotFound(str(current.id))
        return PurgeIdleCheckerAssignmentPayload(id=current.id)

    async def _read_by_pair(
        self, scope: EntityIdentifier, idle_checker_id: IdleCheckerID
    ) -> IdleCheckerAssignmentData:
        """Read the binding back: a relation write answers with the pair alone."""
        result = await self._idle_checker_assignment.lookup_by_pair.run(
            LookupIdleCheckerAssignmentByPairAction(scope=scope, idle_checker_id=idle_checker_id)
        )
        return result.data

    async def admin_search(
        self, input: SearchIdleCheckerAssignmentsInput
    ) -> SearchIdleCheckerAssignmentPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            IdleCheckerAssignmentSearcher,
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
        action_result = await self._idle_checker_assignment.admin_search.run(
            AdminSearchIdleCheckerAssignmentsAction(searcher=searcher)
        )
        return SearchIdleCheckerAssignmentPayload(
            items=[self._data_to_node(item) for item in action_result.items],
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
        searcher = self._build_searcher(
            IdleCheckerAssignmentSearcher,
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
        scopes = [self._scope_entity(ref.scope_type, ref.scope_id) for ref in input.scope.items]
        action_result = await self._idle_checker_assignment.scoped_search.run(
            ScopedSearchIdleCheckerAssignmentsAction(scopes=scopes, searcher=searcher)
        )
        return SearchIdleCheckerAssignmentPayload(
            items=[self._data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_filter(self, f: IdleCheckerAssignmentFilter) -> list[QueryCondition]:
        fields = IdleCheckerAssignmentSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_uuid_filter(f.scope_id, fields.scope_id.filter),
            *self.apply_uuid_filter(f.idle_checker_id, fields.idle_checker_id.filter),
            *self.apply_bool_filter(f.enabled, fields.enabled.filter),
            *self.apply_datetime_filter(f.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(f.updated_at, fields.updated_at.filter),
        ]
        if f.scope_type is not None:
            if f.scope_type.equals is not None:
                conditions.append(
                    fields.scope_type.filter.equals(
                        StringMatchSpec(
                            EntityType.from_name(f.scope_type.equals.value),
                            case_insensitive=False,
                            negated=False,
                        )
                    )
                )
            if f.scope_type.in_ is not None:
                conditions.append(
                    fields.scope_type.filter.in_(
                        StringInMatchSpec(
                            values=[
                                EntityType.from_name(scope_type_dto.value)
                                for scope_type_dto in f.scope_type.in_
                            ],
                            case_insensitive=False,
                            negated=False,
                        )
                    )
                )
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
        fields = IdleCheckerAssignmentSearchableFields.own
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case IdleCheckerAssignmentOrderField.SCOPE_TYPE:
                    result.append(fields.scope_type.order.apply(ascending))
                case IdleCheckerAssignmentOrderField.ENABLED:
                    result.append(fields.enabled.order.apply(ascending))
                case IdleCheckerAssignmentOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case IdleCheckerAssignmentOrderField.UPDATED_AT:
                    result.append(fields.updated_at.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return result

    async def _resolve(self, assignment_id: IdleCheckerAssignmentID) -> IdleCheckerAssignmentData:
        """The pair the id names. Costs READ on the binding's scope."""
        result = await self._idle_checker_assignment.lookup.run(
            LookupIdleCheckerAssignmentAction(assignment_id=assignment_id)
        )
        return result.data

    def _scope_entity(
        self, scope_type: IdleCheckerScopeTypeDTO, scope_id: uuid.UUID
    ) -> EntityIdentifier:
        return RuntimeEntityID(EntityType(scope_type.value), scope_id)

    @staticmethod
    def _data_to_node(data: IdleCheckerAssignmentData) -> IdleCheckerAssignmentNode:
        return IdleCheckerAssignmentNode(
            id=IdleCheckerAssignmentID(data.id),
            scope_type=IdleCheckerScopeTypeDTO(str(data.scope_type)),
            scope_id=data.scope_id,
            idle_checker_id=data.idle_checker_id,
            enabled=data.enabled,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
