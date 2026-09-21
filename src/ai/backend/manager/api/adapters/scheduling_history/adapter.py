"""Scheduling history adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never
from uuid import UUID

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.common.data.filter_specs import StringInMatchSpec, UUIDEqualMatchSpec
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchKernelHistoriesInput,
    AdminSearchReplicaGroupHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    KernelHistoryFilter,
    KernelHistoryOrder,
    ReplicaGroupHistoryFilter,
    ReplicaGroupHistoryOrder,
    RouteHistoryFilter,
    RouteHistoryOrder,
    SchedulingResultFilter,
    ScopedSearchKernelHistoriesInput,
    ScopedSearchReplicaGroupHistoriesInput,
    SessionHistoryFilter,
    SessionHistoryOrder,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    AdminSearchDeploymentHistoriesPayload,
    AdminSearchRouteHistoriesPayload,
    AdminSearchSessionHistoriesPayload,
    DeploymentHistoryNode,
    KernelHistoryNode,
    ReplicaGroupHistoryNode,
    RouteHistoryNode,
    SearchKernelHistoriesPayload,
    SearchReplicaGroupHistoriesPayload,
    SessionHistoryNode,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryOrderField,
    KernelHistoryOrderField,
    OrderDirection,
    ReplicaGroupHistoryOrderField,
    RouteHistoryOrderField,
    SessionHistoryOrderField,
    SubStepResultInfo,
)
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentHistoryData,
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
    RouteHistoryData,
)
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SubStepResult,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.replica_group_history.deprecated_search import (
    DeprecatedReplicaGroupHistoryConditions,
)
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.replica_group_history.searchable_fields import (
    ReplicaGroupHistorySearchableFields,
)
from ai.backend.manager.models.replica_group_history.searchers import ReplicaGroupHistorySearcher
from ai.backend.manager.models.scheduling_history.deprecated_search import (
    DeprecatedDeploymentHistoryConditions,
    DeprecatedKernelSchedulingHistoryConditions,
    DeprecatedRouteHistoryConditions,
    DeprecatedSessionSchedulingHistoryConditions,
)
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.scheduling_history.scopes import (
    DeploymentHistoryTarget,
    DeploymentReplicaGroupHistoryTarget,
    RouteHistoryTarget,
    SessionKernelHistoryTarget,
    SessionSchedulingHistoryTarget,
)
from ai.backend.manager.models.scheduling_history.searchable_fields import (
    DeploymentHistorySearchableFields,
    KernelSchedulingHistorySearchableFields,
    RouteHistorySearchableFields,
    SessionSchedulingHistorySearchableFields,
)
from ai.backend.manager.models.scheduling_history.searchers import (
    DeploymentHistorySearcher,
    KernelSchedulingHistorySearcher,
    RouteHistorySearcher,
    SessionSchedulingHistorySearcher,
)
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.resource_slot.actions.lookup_kernel_owner import (
    LookupKernelOwnerAction,
)
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.scheduling_history.actions.bulk_get_deployment_histories import (
    BulkGetDeploymentHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_kernel_histories import (
    BulkGetKernelHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_route_histories import (
    BulkGetRouteHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.bulk_get_session_histories import (
    BulkGetSessionHistoriesAction,
)
from ai.backend.manager.services.scheduling_history.actions.global_search_replica_group_history import (
    GlobalSearchReplicaGroupHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.lookup_replica_deployment import (
    LookupReplicaDeploymentAction,
)
from ai.backend.manager.services.scheduling_history.actions.scoped_search_replica_group_history import (
    ScopedSearchReplicaGroupHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_deployment_history import (
    SearchDeploymentHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_deployment_scoped_history import (
    SearchDeploymentScopedHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_kernel_history import (
    SearchKernelHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_kernel_scoped_history import (
    SearchKernelScopedHistoryAction,
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
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors

_SESSION_HISTORY_PAGINATION_SPEC = PaginationSpec(
    forward_order=SessionSchedulingHistorySearchableFields.own.created_at.order.apply(
        ascending=False
    ),
    cursor_column=SessionSchedulingHistoryRow.id,
)

_KERNEL_HISTORY_PAGINATION_SPEC = PaginationSpec(
    forward_order=KernelSchedulingHistorySearchableFields.own.created_at.order.apply(
        ascending=False
    ),
    cursor_column=KernelSchedulingHistoryRow.id,
)

_DEPLOYMENT_HISTORY_PAGINATION_SPEC = PaginationSpec(
    forward_order=DeploymentHistorySearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=DeploymentHistoryRow.id,
)

_REPLICA_GROUP_HISTORY_PAGINATION_SPEC = PaginationSpec(
    forward_order=ReplicaGroupHistorySearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=ReplicaGroupHistoryRow.id,
)

_ROUTE_HISTORY_PAGINATION_SPEC = PaginationSpec(
    forward_order=RouteHistorySearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=RouteHistoryRow.id,
)


class SchedulingHistoryAdapter(BaseAdapter):
    """Adapter for scheduling history domain operations."""

    _scheduling_history: SchedulingHistoryProcessors
    _resource_slot: ResourceSlotProcessors

    def __init__(
        self,
        scheduling_history: SchedulingHistoryProcessors,
        resource_slot: ResourceSlotProcessors,
    ) -> None:
        self._scheduling_history = scheduling_history
        self._resource_slot = resource_slot

    # ========== Batch Load (DataLoader) ==========

    async def batch_load_session_histories_by_ids(
        self, ids: Sequence[SessionSchedulingHistoryID]
    ) -> list[SessionHistoryNode | Exception | None]:
        """Batch load session scheduling histories for DataLoader use, checked per session."""
        if not ids:
            return []
        history_ids = [SessionSchedulingHistoryID(history_id) for history_id in ids]
        return await self.batch_load_fields(
            self._scheduling_history.bulk_get_session_histories,
            BulkGetSessionHistoriesAction(ids=history_ids),
            history_ids,
            self._session_data_to_dto,
        )

    async def batch_load_kernel_histories_by_ids(
        self, ids: Sequence[KernelSchedulingHistoryID]
    ) -> list[KernelHistoryNode | Exception | None]:
        """Batch load kernel scheduling histories for DataLoader use, checked per session."""
        if not ids:
            return []
        return await self.batch_load_fields(
            self._scheduling_history.bulk_get_kernel_histories,
            BulkGetKernelHistoriesAction(ids=ids),
            ids,
            self._kernel_data_to_dto,
        )

    async def batch_load_deployment_histories_by_ids(
        self, ids: Sequence[DeploymentHistoryID]
    ) -> list[DeploymentHistoryNode | Exception | None]:
        """Batch load deployment histories for DataLoader use, checked per deployment."""
        if not ids:
            return []
        history_ids = [DeploymentHistoryID(history_id) for history_id in ids]
        return await self.batch_load_fields(
            self._scheduling_history.bulk_get_deployment_histories,
            BulkGetDeploymentHistoriesAction(ids=history_ids),
            history_ids,
            self._deployment_data_to_dto,
        )

    async def batch_load_route_histories_by_ids(
        self, ids: Sequence[RouteHistoryID]
    ) -> list[RouteHistoryNode | Exception | None]:
        """Batch load route histories for DataLoader use, checked per deployment."""
        if not ids:
            return []
        history_ids = [RouteHistoryID(history_id) for history_id in ids]
        return await self.batch_load_fields(
            self._scheduling_history.bulk_get_route_histories,
            BulkGetRouteHistoriesAction(ids=history_ids),
            history_ids,
            self._route_data_to_dto,
        )

    # ========== Session History ==========

    async def admin_search_session_history(
        self,
        input: AdminSearchSessionHistoriesInput,
    ) -> AdminSearchSessionHistoriesPayload:
        """Search session scheduling histories (admin, no scope)."""
        action_result = await self._scheduling_history.search_session_history.run(
            SearchSessionHistoryAction(
                searcher=GlobalSearcher(used_by=(), searcher=self._build_session_searcher(input))
            )
        )
        return AdminSearchSessionHistoriesPayload(
            items=[self._session_data_to_dto(h) for h in action_result.items],
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
        scope = SessionSchedulingHistoryTarget(session_id=session_id)
        action_result = await self._scheduling_history.search_session_scoped_history.run(
            SearchSessionScopedHistoryAction(
                session_id=SessionID(session_id),
                scope=scope,
                searcher=self._build_session_searcher(input),
            )
        )
        return AdminSearchSessionHistoriesPayload(
            items=[self._session_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_session_searcher(
        self, input: AdminSearchSessionHistoriesInput
    ) -> SessionSchedulingHistorySearcher:
        return self._build_searcher(
            SessionSchedulingHistorySearcher,
            conditions=self._convert_session_filter(input.filter) if input.filter else [],
            orders=self._convert_session_orders(input.order) if input.order else [],
            pagination_spec=_SESSION_HISTORY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_session_filter(self, filter: SessionHistoryFilter) -> list[QueryCondition]:
        fields = SessionSchedulingHistorySearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_uuid_filter(filter.session_id, fields.session_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._convert_result_filter(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(
                filter.message, DeprecatedSessionSchedulingHistoryConditions.message
            ),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.updated_at, fields.updated_at.filter),
        ]
        if filter.AND:
            for sub in filter.AND:
                conditions.extend(self._convert_session_filter(sub))
        if filter.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter.OR:
                or_conds.extend(self._convert_session_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter.NOT:
                not_conds.extend(self._convert_session_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    @staticmethod
    def _convert_session_orders(order: list[SessionHistoryOrder]) -> list[QueryOrder]:
        fields = SessionSchedulingHistorySearchableFields.own
        orders: list[QueryOrder] = []
        for o in order:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case SessionHistoryOrderField.CREATED_AT:
                    orders.append(fields.created_at.order.apply(ascending))
                case SessionHistoryOrderField.UPDATED_AT:
                    orders.append(fields.updated_at.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return orders

    # ========== Kernel History ==========

    async def admin_search_kernel_history(
        self,
        input: AdminSearchKernelHistoriesInput,
    ) -> SearchKernelHistoriesPayload:
        """Search kernel scheduling histories (admin, no scope)."""
        searcher = self._build_kernel_searcher(
            self._convert_kernel_filter(input.filter) if input.filter else [],
            self._convert_kernel_orders(input.order) if input.order else [],
            input,
        )
        action_result = await self._scheduling_history.search_kernel_history.run(
            SearchKernelHistoryAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return SearchKernelHistoriesPayload(
            items=[self._kernel_data_to_dto(h) for h in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def scoped_search_kernel_history(
        self,
        input: ScopedSearchKernelHistoriesInput,
    ) -> SearchKernelHistoriesPayload:
        """Search kernel scheduling histories under a non-admin scope."""
        conditions = self._convert_kernel_filter(input.filter) if input.filter else []
        orders = self._convert_kernel_orders(input.order) if input.order else []
        kernel_items = input.scope.kernel or []
        session_items = input.scope.session or []
        # TODO: Drop this rejection once the scoped search becomes a bulk action.
        # The scope input is already list-shaped and its items are meant to be
        # OR'd, but SearchKernelScopedHistoryAction is a single-target
        # BaseScopeAction, so only one item is dispatchable today.
        if len(kernel_items) + len(session_items) != 1:
            raise InvalidAPIParameters(
                "Kernel scheduling history scope accepts exactly one scope item"
            )
        # TODO: Pass KernelKernelHistoryTarget(kernel_id=...) once virtual entities
        # land and a kernel becomes a scope of its own. Kernels hold no permission
        # records today, so a kernel scope item is converted to a target on its
        # owning session and narrowed back down with a kernel_id query condition.
        if kernel_items:
            kernel_id = KernelId(kernel_items[0].value)
            owner = await self._resource_slot.lookup_kernel_owner.run(
                LookupKernelOwnerAction(kernel_id=KernelID(kernel_id))
            )
            session_id = SessionId(owner.entity_id())
            conditions.append(
                KernelSchedulingHistorySearchableFields.own.kernel_id.filter.equals(
                    UUIDEqualMatchSpec(value=kernel_id, negated=False)
                )
            )
        else:
            session_id = SessionId(session_items[0].value)
        action_result = await self._scheduling_history.search_kernel_scoped_history.run(
            SearchKernelScopedHistoryAction(
                target=SessionKernelHistoryTarget(session_id=session_id),
                searcher=self._build_kernel_searcher(conditions, orders, input),
            )
        )
        return SearchKernelHistoriesPayload(
            items=[self._kernel_data_to_dto(h) for h in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_kernel_searcher(
        self,
        conditions: list[QueryCondition],
        orders: list[QueryOrder],
        input: AdminSearchKernelHistoriesInput | ScopedSearchKernelHistoriesInput,
    ) -> KernelSchedulingHistorySearcher:
        return self._build_searcher(
            KernelSchedulingHistorySearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_KERNEL_HISTORY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_kernel_filter(self, filter: KernelHistoryFilter) -> list[QueryCondition]:
        fields = KernelSchedulingHistorySearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_uuid_filter(filter.kernel_id, fields.kernel_id.filter),
            *self.apply_uuid_filter(filter.session_id, fields.session_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._convert_result_filter(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(
                filter.message, DeprecatedKernelSchedulingHistoryConditions.message
            ),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.updated_at, fields.updated_at.filter),
        ]
        if filter.AND:
            for sub in filter.AND:
                conditions.extend(self._convert_kernel_filter(sub))
        if filter.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter.OR:
                or_conds.extend(self._convert_kernel_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter.NOT:
                not_conds.extend(self._convert_kernel_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    @staticmethod
    def _convert_kernel_orders(order: list[KernelHistoryOrder]) -> list[QueryOrder]:
        fields = KernelSchedulingHistorySearchableFields.own
        orders: list[QueryOrder] = []
        for o in order:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case KernelHistoryOrderField.CREATED_AT:
                    orders.append(fields.created_at.order.apply(ascending))
                case KernelHistoryOrderField.UPDATED_AT:
                    orders.append(fields.updated_at.order.apply(ascending))
                case KernelHistoryOrderField.PHASE:
                    orders.append(fields.phase.order.apply(ascending))
                case KernelHistoryOrderField.FROM_STATUS:
                    orders.append(fields.from_status.order.apply(ascending))
                case KernelHistoryOrderField.TO_STATUS:
                    orders.append(fields.to_status.order.apply(ascending))
                case KernelHistoryOrderField.RESULT:
                    orders.append(fields.result.order.apply(ascending))
                case KernelHistoryOrderField.ATTEMPTS:
                    orders.append(fields.attempts.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return orders

    # ========== Deployment History ==========

    async def admin_search_deployment_history(
        self,
        input: AdminSearchDeploymentHistoriesInput,
    ) -> AdminSearchDeploymentHistoriesPayload:
        """Search deployment histories (admin, no scope)."""
        action_result = await self._scheduling_history.search_deployment_history.run(
            SearchDeploymentHistoryAction(
                searcher=GlobalSearcher(used_by=(), searcher=self._build_deployment_searcher(input))
            )
        )
        return AdminSearchDeploymentHistoriesPayload(
            items=[self._deployment_data_to_dto(h) for h in action_result.items],
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
        scope = DeploymentHistoryTarget(deployment_id=deployment_id)
        action_result = await self._scheduling_history.search_deployment_scoped_history.run(
            SearchDeploymentScopedHistoryAction(
                deployment_id=DeploymentID(deployment_id),
                scope=scope,
                searcher=self._build_deployment_searcher(input),
            )
        )
        return AdminSearchDeploymentHistoriesPayload(
            items=[self._deployment_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_deployment_searcher(
        self, input: AdminSearchDeploymentHistoriesInput
    ) -> DeploymentHistorySearcher:
        return self._build_searcher(
            DeploymentHistorySearcher,
            conditions=self._convert_deployment_filter(input.filter) if input.filter else [],
            orders=self._convert_deployment_orders(input.order) if input.order else [],
            pagination_spec=_DEPLOYMENT_HISTORY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_deployment_filter(self, filter: DeploymentHistoryFilter) -> list[QueryCondition]:
        fields = DeploymentHistorySearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_uuid_filter(filter.deployment_id, fields.deployment_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._convert_result_filter(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(
                filter.message, DeprecatedDeploymentHistoryConditions.message
            ),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.updated_at, fields.updated_at.filter),
        ]
        if filter.AND:
            for sub in filter.AND:
                conditions.extend(self._convert_deployment_filter(sub))
        if filter.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter.OR:
                or_conds.extend(self._convert_deployment_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter.NOT:
                not_conds.extend(self._convert_deployment_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    @staticmethod
    def _convert_deployment_orders(order: list[DeploymentHistoryOrder]) -> list[QueryOrder]:
        fields = DeploymentHistorySearchableFields.own
        orders: list[QueryOrder] = []
        for o in order:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case DeploymentHistoryOrderField.CREATED_AT:
                    orders.append(fields.created_at.order.apply(ascending))
                case DeploymentHistoryOrderField.UPDATED_AT:
                    orders.append(fields.updated_at.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return orders

    # ========== Replica Group History ==========

    async def admin_search_replica_group_history(
        self,
        input: AdminSearchReplicaGroupHistoriesInput,
    ) -> SearchReplicaGroupHistoriesPayload:
        """Search replica-group scheduling histories (admin, no scope)."""
        action_result = await self._scheduling_history.global_search_replica_group_history.run(
            GlobalSearchReplicaGroupHistoryAction(
                searcher=GlobalSearcher(
                    used_by=(), searcher=self._build_replica_group_searcher(input)
                )
            )
        )
        return SearchReplicaGroupHistoriesPayload(
            items=[self._replica_group_data_to_dto(h) for h in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def scoped_search_replica_group_history(
        self,
        input: ScopedSearchReplicaGroupHistoriesInput,
    ) -> SearchReplicaGroupHistoriesPayload:
        """Search replica-group scheduling histories under a non-admin scope."""
        deployment_items = input.scope.deployment or []
        # TODO: Drop this rejection once the scoped search becomes a bulk action.
        # The scope input is already list-shaped and its items are meant to be
        # OR'd, but ScopedSearchReplicaGroupHistoryAction is a single-target
        # BaseScopeAction, so only one item is dispatchable today.
        if len(deployment_items) != 1:
            raise InvalidAPIParameters(
                "Replica-group scheduling history scope accepts exactly one scope item"
            )
        # A replica group is not an RBAC scope of its own, so its history is scoped by
        # the owning deployment.
        deployment_id = DeploymentID(deployment_items[0].value)
        action_result = await self._scheduling_history.scoped_search_replica_group_history.run(
            ScopedSearchReplicaGroupHistoryAction(
                target=DeploymentReplicaGroupHistoryTarget(deployment_id=deployment_id),
                searcher=self._build_replica_group_searcher(input),
            )
        )
        return SearchReplicaGroupHistoriesPayload(
            items=[self._replica_group_data_to_dto(h) for h in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_replica_group_searcher(
        self,
        input: AdminSearchReplicaGroupHistoriesInput | ScopedSearchReplicaGroupHistoriesInput,
    ) -> ReplicaGroupHistorySearcher:
        return self._build_searcher(
            ReplicaGroupHistorySearcher,
            conditions=self._convert_replica_group_filter(input.filter) if input.filter else [],
            orders=self._convert_replica_group_orders(input.order) if input.order else [],
            pagination_spec=_REPLICA_GROUP_HISTORY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_replica_group_filter(
        self, filter: ReplicaGroupHistoryFilter
    ) -> list[QueryCondition]:
        fields = ReplicaGroupHistorySearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_uuid_filter(filter.deployment_id, fields.deployment_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._convert_result_filter(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(
                filter.message, DeprecatedReplicaGroupHistoryConditions.message
            ),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.updated_at, fields.updated_at.filter),
        ]
        if filter.category:
            conditions.append(
                fields.category.filter.in_([
                    ReplicaGroupHandlerCategory(c) for c in filter.category
                ])
            )
        if filter.AND:
            for sub in filter.AND:
                conditions.extend(self._convert_replica_group_filter(sub))
        if filter.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter.OR:
                or_conds.extend(self._convert_replica_group_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter.NOT:
                not_conds.extend(self._convert_replica_group_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    @staticmethod
    def _convert_replica_group_orders(order: list[ReplicaGroupHistoryOrder]) -> list[QueryOrder]:
        fields = ReplicaGroupHistorySearchableFields.own
        orders: list[QueryOrder] = []
        for o in order:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case ReplicaGroupHistoryOrderField.CREATED_AT:
                    orders.append(fields.created_at.order.apply(ascending))
                case ReplicaGroupHistoryOrderField.UPDATED_AT:
                    orders.append(fields.updated_at.order.apply(ascending))
                case ReplicaGroupHistoryOrderField.PHASE:
                    orders.append(fields.phase.order.apply(ascending))
                case ReplicaGroupHistoryOrderField.FROM_STATUS:
                    orders.append(fields.from_status.order.apply(ascending))
                case ReplicaGroupHistoryOrderField.TO_STATUS:
                    orders.append(fields.to_status.order.apply(ascending))
                case ReplicaGroupHistoryOrderField.RESULT:
                    orders.append(fields.result.order.apply(ascending))
                case ReplicaGroupHistoryOrderField.ATTEMPTS:
                    orders.append(fields.attempts.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return orders

    # ========== Route History ==========

    async def admin_search_route_history(
        self,
        input: AdminSearchRouteHistoriesInput,
    ) -> AdminSearchRouteHistoriesPayload:
        """Search route histories (admin, no scope)."""
        action_result = await self._scheduling_history.search_route_history.run(
            SearchRouteHistoryAction(
                searcher=GlobalSearcher(used_by=(), searcher=self._build_route_searcher(input))
            )
        )
        return AdminSearchRouteHistoriesPayload(
            items=[self._route_data_to_dto(h) for h in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def route_scoped_search(
        self,
        route_id: UUID,
        input: AdminSearchRouteHistoriesInput,
    ) -> AdminSearchRouteHistoriesPayload:
        """Search route histories scoped to a route.

        A replica carries no permission of its own, so the deployment it serves is read
        first and the read is answered for by that deployment.
        """
        replica_id = ReplicaID(route_id)
        owner = await self._scheduling_history.lookup_replica_deployment.run(
            LookupReplicaDeploymentAction(replica_id=replica_id)
        )
        scope = RouteHistoryTarget(
            deployment_id=DeploymentID(owner.entity_id()), route_id=replica_id
        )
        action_result = await self._scheduling_history.search_route_scoped_history.run(
            SearchRouteScopedHistoryAction(scope=scope, searcher=self._build_route_searcher(input))
        )
        return AdminSearchRouteHistoriesPayload(
            items=[self._route_data_to_dto(h) for h in action_result.histories],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_route_searcher(self, input: AdminSearchRouteHistoriesInput) -> RouteHistorySearcher:
        return self._build_searcher(
            RouteHistorySearcher,
            conditions=self._convert_route_filter(input.filter) if input.filter else [],
            orders=self._convert_route_orders(input.order) if input.order else [],
            pagination_spec=_ROUTE_HISTORY_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_route_filter(self, filter: RouteHistoryFilter) -> list[QueryCondition]:
        fields = RouteHistorySearchableFields.own
        conditions = [
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_uuid_filter(filter.route_id, fields.route_id.filter),
            *self.apply_uuid_filter(filter.deployment_id, fields.deployment_id.filter),
            *self.apply_string_filter(filter.phase, fields.phase.filter),
            *self._status_in(filter.from_status, fields.from_status.filter),
            *self._status_in(filter.to_status, fields.to_status.filter),
            *self._convert_result_filter(filter.result, fields.result.filter),
            *self.apply_string_filter(filter.error_code, fields.error_code.filter),
            *self.apply_string_filter(filter.message, DeprecatedRouteHistoryConditions.message),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.updated_at, fields.updated_at.filter),
        ]
        if filter.AND:
            for sub in filter.AND:
                conditions.extend(self._convert_route_filter(sub))
        if filter.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter.OR:
                or_conds.extend(self._convert_route_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter.NOT:
                not_conds.extend(self._convert_route_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    @staticmethod
    def _convert_route_orders(order: list[RouteHistoryOrder]) -> list[QueryOrder]:
        fields = RouteHistorySearchableFields.own
        orders: list[QueryOrder] = []
        for o in order:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case RouteHistoryOrderField.CREATED_AT:
                    orders.append(fields.created_at.order.apply(ascending))
                case RouteHistoryOrderField.UPDATED_AT:
                    orders.append(fields.updated_at.order.apply(ascending))
                case _:
                    assert_never(o.field)
        return orders

    # ========== Shared filter conversion ==========

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

    @staticmethod
    def _convert_result_filter(
        result: SchedulingResultFilter | None,
        conditions: EnumConditions[SchedulingResult],
    ) -> list[QueryCondition]:
        """Apply every operation the scheduling-result filter sets."""
        if result is None:
            return []
        applied: list[QueryCondition] = []
        if result.equals is not None:
            applied.append(conditions.equals(SchedulingResult(result.equals)))
        if result.in_:
            applied.append(conditions.in_([SchedulingResult(v) for v in result.in_]))
        if result.not_equals is not None:
            applied.append(conditions.not_equals(SchedulingResult(result.not_equals)))
        if result.not_in:
            applied.append(conditions.not_in([SchedulingResult(v) for v in result.not_in]))
        return applied

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
            field_id=data.id,
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
    def _kernel_data_to_dto(data: KernelSchedulingHistoryData) -> KernelHistoryNode:
        return KernelHistoryNode(
            id=data.id,
            field_id=data.id,
            kernel_id=data.kernel_id,
            session_id=data.session_id,
            phase=data.phase,
            from_status=data.from_status.value if data.from_status else None,
            to_status=data.to_status.value if data.to_status else None,
            result=data.result.value,
            error_code=data.error_code,
            message=data.message,
            attempts=data.attempts,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _deployment_data_to_dto(data: DeploymentHistoryData) -> DeploymentHistoryNode:
        return DeploymentHistoryNode(
            id=data.id,
            field_id=data.id,
            deployment_id=data.deployment_id,
            category=data.handler_category.value,
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
    def _replica_group_data_to_dto(data: ReplicaGroupHistoryData) -> ReplicaGroupHistoryNode:
        return ReplicaGroupHistoryNode(
            id=data.id,
            field_id=data.id,
            deployment_id=data.deployment_id,
            category=data.category.value,
            phase=data.phase,
            from_status=data.from_status,
            to_status=data.to_status,
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
            field_id=data.id,
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
