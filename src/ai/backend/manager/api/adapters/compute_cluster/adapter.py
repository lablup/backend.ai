"""Compute cluster adapter bridging DTOs and Processors. Every operation is superadmin-only."""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    ComputeClusterFilter,
    ComputeClusterOrder,
    CreateComputeClusterInput,
    SearchComputeClustersInput,
    UpdateComputeClusterInput,
)
from ai.backend.common.dto.manager.v2.compute_cluster.response import (
    ComputeClusterNode,
    CreateComputeClusterPayload,
    PurgeComputeClusterPayload,
    SearchComputeClustersPayload,
    UpdateComputeClusterPayload,
)
from ai.backend.common.dto.manager.v2.compute_cluster.types import (
    ComputeClusterOrderField,
    OrderDirection,
)
from ai.backend.common.dto.manager.v2.compute_cluster.types import (
    ComputeClusterStatus as ComputeClusterStatusDTO,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData, ComputeClusterStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.compute_cluster.searchable_fields import (
    ComputeClusterSearchableFields,
)
from ai.backend.manager.models.compute_cluster.searchers import ComputeClusterSearcher
from ai.backend.manager.models.compute_cluster.updaters import ComputeClusterUpdater
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.compute_cluster.actions.bulk_get import (
    BulkGetComputeClustersAction,
)
from ai.backend.manager.services.compute_cluster.actions.create import (
    CreateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.get import GetComputeClusterAction
from ai.backend.manager.services.compute_cluster.actions.global_search import (
    GlobalSearchComputeClustersAction,
)
from ai.backend.manager.services.compute_cluster.actions.purge import (
    PurgeComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.update import (
    UpdateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.processors import ComputeClusterProcessors
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("ComputeClusterAdapter",)

_PAGINATION_SPEC = PaginationSpec(
    forward_order=ComputeClusterSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=ComputeClusterRow.id,
)


class ComputeClusterAdapter(BaseAdapter):
    """Adapter for compute cluster operations. The kubeconfig is accepted, never returned."""

    _compute_cluster: ComputeClusterProcessors

    def __init__(self, compute_cluster: ComputeClusterProcessors) -> None:
        self._compute_cluster = compute_cluster

    async def get(self, cluster_id: ComputeClusterID) -> ComputeClusterNode:
        result = await self._compute_cluster.get.run(GetComputeClusterAction(id=cluster_id))
        return self._data_to_node(result.data)

    async def bulk_get_ids(
        self, ids: Sequence[ComputeClusterID]
    ) -> list[ComputeClusterNode | Exception | None]:
        """One answer per id for DataLoader use: the node, ``None`` for a missing id, or the
        denial."""
        if not ids:
            return []
        result = await self._compute_cluster.bulk_get_ids.run(
            BulkGetComputeClustersAction(ids=list(ids))
        )
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def global_search(
        self, input: SearchComputeClustersInput
    ) -> SearchComputeClustersPayload:
        """Search every compute cluster, by cursor or by offset as the request names."""
        options = PaginationOptions(
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        limit = input.limit
        if limit is None and not options.has_cursor:
            limit = DEFAULT_PAGE_LIMIT
        searcher = self._build_searcher(
            ComputeClusterSearcher,
            conditions=self._convert_filter(input.filter) if input.filter else [],
            orders=self._convert_orders(input.order) if input.order else [],
            pagination_spec=_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=limit,
            offset=input.offset,
        )
        result = await self._compute_cluster.global_search.run(
            GlobalSearchComputeClustersAction(
                searcher=GlobalSearcher(used_by=(), searcher=searcher)
            )
        )
        return SearchComputeClustersPayload(
            items=[self._data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create(self, input: CreateComputeClusterInput) -> CreateComputeClusterPayload:
        result = await self._compute_cluster.create.run(
            CreateComputeClusterAction(
                name=input.name,
                description=input.description,
                api_server=input.api_server,
                kubeconfig=input.kubeconfig,
                namespace_prefix=input.namespace_prefix,
                gateway_addr=input.gateway_addr,
                gateway_public_key=input.gateway_public_key,
            )
        )
        return CreateComputeClusterPayload(compute_cluster=self._data_to_node(result.data))

    async def update(
        self, cluster_id: ComputeClusterID, input: UpdateComputeClusterInput
    ) -> UpdateComputeClusterPayload:
        result = await self._compute_cluster.update.run(
            UpdateComputeClusterAction(
                updater=ComputeClusterUpdater(
                    compute_cluster_id=cluster_id,
                    description=TriState.from_unset(input.description),
                    api_server=OptionalState.from_unset(input.api_server),
                    namespace_prefix=OptionalState.from_unset(input.namespace_prefix),
                    gateway_addr=TriState.from_unset(input.gateway_addr),
                    gateway_public_key=TriState.from_unset(input.gateway_public_key),
                    status=OptionalState.from_unset(input.status).map(
                        lambda status: ComputeClusterStatus(status.value)
                    ),
                ),
                kubeconfig=OptionalState.from_unset(input.kubeconfig),
            )
        )
        return UpdateComputeClusterPayload(compute_cluster=self._data_to_node(result.data))

    async def purge(self, cluster_id: ComputeClusterID) -> PurgeComputeClusterPayload:
        result = await self._compute_cluster.purge.run(PurgeComputeClusterAction(id=cluster_id))
        return PurgeComputeClusterPayload(entity_id=result.data.id)

    @staticmethod
    def _data_to_node(data: ComputeClusterData) -> ComputeClusterNode:
        return ComputeClusterNode(
            id=data.id,
            entity_id=data.id,
            name=data.name,
            description=data.description,
            api_server=data.api_server,
            namespace_prefix=data.namespace_prefix,
            gateway_addr=data.gateway_addr,
            gateway_public_key=data.gateway_public_key,
            status=ComputeClusterStatusDTO(data.status.value),
            status_changed_at=data.status_changed_at,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def _convert_orders(self, orders: list[ComputeClusterOrder]) -> list[QueryOrder]:
        fields = ComputeClusterSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case ComputeClusterOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
                case ComputeClusterOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case _:
                    assert_never(order.field)
        return result

    def _convert_filter(self, filter: ComputeClusterFilter) -> list[QueryCondition]:
        fields = ComputeClusterSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_uuid_filter(filter.entity_id, fields.id.filter),
            *self.apply_string_filter(filter.name, fields.name.filter),
            *self.apply_enum_filter(filter.status, fields.status.filter),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
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
