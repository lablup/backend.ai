from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import assert_never

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.dto.manager.v2.common import PartialBulkFailure, PartialBulkPayload
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    CreateRetentionPolicyInput,
    PartialBulkPurgeRetentionPoliciesInput,
    PartialBulkUpdateRetentionPoliciesInput,
    RetentionPolicyFilter,
    RetentionPolicyOrder,
    SearchRetentionPoliciesInput,
    UpdateRetentionPolicyInput,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    CreateRetentionPolicyPayload,
    PurgeRetentionPolicyPayload,
    RetentionPolicyNode,
    SearchRetentionPoliciesPayload,
    UpdateRetentionPolicyPayload,
)
from ai.backend.common.dto.manager.v2.retention_policy.types import RetentionPolicyOrderField
from ai.backend.manager.actions.v2.bulk.result import PartialBulkResult
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.retention.creators import RetentionPolicyCreator
from ai.backend.manager.models.retention.purgers import RetentionPolicyPurger
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.retention.searchable_fields import (
    RetentionPolicySearchableFields,
)
from ai.backend.manager.models.retention.searchers import RetentionPolicySearcher
from ai.backend.manager.models.retention.updaters import RetentionPolicyUpdater
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.retention_policy.actions.bulk_get import (
    BulkGetRetentionPoliciesAction,
)
from ai.backend.manager.services.retention_policy.actions.create import (
    CreateRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.actions.get import GetRetentionPolicyAction
from ai.backend.manager.services.retention_policy.actions.partial_bulk_purge import (
    PartialBulkPurgeRetentionPoliciesAction,
)
from ai.backend.manager.services.retention_policy.actions.partial_bulk_update import (
    PartialBulkUpdateRetentionPoliciesAction,
)
from ai.backend.manager.services.retention_policy.actions.purge import (
    PurgeRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.actions.search import (
    SearchRetentionPoliciesAction,
)
from ai.backend.manager.services.retention_policy.actions.update import (
    UpdateRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.processors import RetentionPolicyProcessors
from ai.backend.manager.types import OptionalState


def _retention_policy_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RetentionPolicySearchableFields.own.category.order.apply(ascending=True),
        cursor_column=RetentionPolicyRow.id,
    )


class RetentionPolicyAdapter(BaseAdapter):
    _retention_policy: RetentionPolicyProcessors

    def __init__(self, retention_policy: RetentionPolicyProcessors) -> None:
        self._retention_policy = retention_policy

    async def search(
        self,
        input: SearchRetentionPoliciesInput,
    ) -> SearchRetentionPoliciesPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            RetentionPolicySearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_retention_policy_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._retention_policy.global_search.run(
            SearchRetentionPoliciesAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return SearchRetentionPoliciesPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, policy_id: RetentionPolicyID) -> RetentionPolicyNode:
        result = await self._retention_policy.get.run(GetRetentionPolicyAction(policy_id=policy_id))
        return self._data_to_node(result.data)

    async def batch_load_by_ids(
        self, ids: Sequence[RetentionPolicyID]
    ) -> list[RetentionPolicyNode | Exception | None]:
        """Batch load retention policies by id for DataLoader use, one answer per id."""
        if not ids:
            return []
        result = await self._retention_policy.bulk_get.run(BulkGetRetentionPoliciesAction(ids=ids))
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def create(
        self,
        input: CreateRetentionPolicyInput,
    ) -> CreateRetentionPolicyPayload:
        creator = RetentionPolicyCreator(
            category=input.category,
            retention_period=timedelta(days=input.retention_period_days),
            enabled=input.enabled,
        )
        result = await self._retention_policy.global_create.run(
            CreateRetentionPolicyAction(creator=creator)
        )
        return CreateRetentionPolicyPayload(policy=self._data_to_node(result.data))

    async def update(
        self,
        input: UpdateRetentionPolicyInput,
    ) -> UpdateRetentionPolicyPayload:
        result = await self._retention_policy.update.run(
            UpdateRetentionPolicyAction(updater=self._to_updater(input))
        )
        return UpdateRetentionPolicyPayload(policy=self._data_to_node(result.data))

    async def purge(self, policy_id: RetentionPolicyID) -> PurgeRetentionPolicyPayload:
        purger = RetentionPolicyPurger(policy_id=policy_id)
        result = await self._retention_policy.purge.run(PurgeRetentionPolicyAction(purger=purger))
        return PurgeRetentionPolicyPayload(id=result.data.id, entity_id=result.data.id)

    async def partial_bulk_update(
        self, input: PartialBulkUpdateRetentionPoliciesInput
    ) -> PartialBulkPayload[RetentionPolicyNode]:
        """Update several retention policies, answering for each one."""
        result = await self._retention_policy.partial_bulk_update.run(
            PartialBulkUpdateRetentionPoliciesAction(
                updaters=[self._to_updater(item) for item in input.items]
            )
        )
        return self._to_partial_bulk_payload(result)

    async def partial_bulk_purge(
        self, input: PartialBulkPurgeRetentionPoliciesInput
    ) -> PartialBulkPayload[RetentionPolicyNode]:
        """Purge several retention policies, answering for each one."""
        result = await self._retention_policy.partial_bulk_purge.run(
            PartialBulkPurgeRetentionPoliciesAction(ids=input.ids)
        )
        return self._to_partial_bulk_payload(result)

    def _to_updater(self, input: UpdateRetentionPolicyInput) -> RetentionPolicyUpdater:
        return RetentionPolicyUpdater(
            policy_id=input.id,
            category=(
                OptionalState.update(input.category)
                if input.category is not None
                else OptionalState.nop()
            ),
            retention_period=(
                OptionalState.update(timedelta(days=input.retention_period_days))
                if input.retention_period_days is not None
                else OptionalState.nop()
            ),
            enabled=(
                OptionalState.update(input.enabled)
                if input.enabled is not None
                else OptionalState.nop()
            ),
        )

    def _to_partial_bulk_payload(
        self, result: PartialBulkResult[RetentionPolicyData]
    ) -> PartialBulkPayload[RetentionPolicyNode]:
        return PartialBulkPayload[RetentionPolicyNode](
            successes=[
                self._data_to_node(item.value) for item in result.items if item.value is not None
            ],
            failed=[
                PartialBulkFailure(id=item.entity_id, message=str(item.error))
                for item in result.items
                if item.error is not None
            ],
        )

    def _convert_filter(self, filter_: RetentionPolicyFilter) -> list[QueryCondition]:
        fields = RetentionPolicySearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_bool_filter(filter_.enabled, fields.enabled.filter),
            *self.apply_uuid_filter(filter_.entity_id, fields.id.filter),
        ]
        if filter_.category is not None:
            conditions.append(fields.category.filter.equals(filter_.category))
        return conditions

    def _convert_orders(self, orders: list[RetentionPolicyOrder]) -> list[QueryOrder]:
        fields = RetentionPolicySearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case RetentionPolicyOrderField.CATEGORY:
                    result.append(fields.category.order.apply(ascending))
                case RetentionPolicyOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case RetentionPolicyOrderField.LAST_SWEPT_AT:
                    result.append(fields.last_swept_at.order.apply(ascending))
                case _:
                    assert_never(order.field)
        return result

    @staticmethod
    def _data_to_node(data: RetentionPolicyData) -> RetentionPolicyNode:
        return RetentionPolicyNode(
            id=data.id,
            entity_id=data.entity_id(),
            category=data.category,
            retention_period_days=data.retention_period.days,
            enabled=data.enabled,
            last_swept_at=data.last_swept_at,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
