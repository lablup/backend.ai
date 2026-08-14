from __future__ import annotations

from datetime import timedelta

from ai.backend.common.dto.manager.v2.retention_policy.request import (
    CreateRetentionPolicyInput,
    RetentionPolicyFilter,
    RetentionPolicyOrder,
    SearchRetentionPoliciesInput,
    UpdateRetentionPolicyInput,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    CreateRetentionPolicyPayload,
    DeleteRetentionPolicyPayload,
    PurgeRetentionPolicyPayload,
    RetentionPolicyNode,
    SearchRetentionPoliciesPayload,
    UpdateRetentionPolicyPayload,
)
from ai.backend.common.dto.manager.v2.retention_policy.types import RetentionPolicyOrderField
from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.errors.retention import RetentionPolicyNotFound
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.retention.conditions import RetentionPolicyConditions
from ai.backend.manager.models.retention.creators import RetentionPolicyCreator
from ai.backend.manager.models.retention.orders import RetentionPolicyOrders
from ai.backend.manager.models.retention.purgers import RetentionPolicyPurger
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.retention.updaters import RetentionPolicyUpdater
from ai.backend.manager.repositories.retention_policy.searchers import RetentionPolicySearcher
from ai.backend.manager.services.retention_policy.actions.create import (
    CreateRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.actions.delete import (
    DeleteRetentionPolicyAction,
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
from ai.backend.manager.types import OptionalState


def _retention_policy_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RetentionPolicyOrders.category(ascending=True),
        backward_order=RetentionPolicyOrders.category(ascending=False),
        forward_condition_factory=RetentionPolicyConditions.by_cursor_forward,
        backward_condition_factory=RetentionPolicyConditions.by_cursor_backward,
        tiebreaker_order=RetentionPolicyRow.id.asc(),
    )


class RetentionPolicyAdapter(BaseAdapter):
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
        result = await self._processors.retention_policy.search.run(
            SearchRetentionPoliciesAction(searcher=searcher)
        )
        return SearchRetentionPoliciesPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, policy_id: RetentionPolicyID) -> RetentionPolicyNode:
        conditions: list[QueryCondition] = [lambda: RetentionPolicyRow.id == policy_id]
        searcher = self._build_searcher(
            RetentionPolicySearcher,
            conditions=conditions,
            orders=[],
            pagination_spec=_retention_policy_pagination_spec(),
            limit=1,
        )
        result = await self._processors.retention_policy.search.run(
            SearchRetentionPoliciesAction(searcher=searcher)
        )
        if not result.items:
            raise RetentionPolicyNotFound()
        return self._data_to_node(result.items[0])

    async def create(
        self,
        input: CreateRetentionPolicyInput,
    ) -> CreateRetentionPolicyPayload:
        creator = RetentionPolicyCreator(
            category=input.category,
            retention_period=timedelta(days=input.retention_period_days),
            enabled=input.enabled,
        )
        result = await self._processors.retention_policy.create.run(
            CreateRetentionPolicyAction(creator=creator)
        )
        return CreateRetentionPolicyPayload(policy=self._data_to_node(result.data))

    async def update(
        self,
        input: UpdateRetentionPolicyInput,
    ) -> UpdateRetentionPolicyPayload:
        updater = RetentionPolicyUpdater(
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
        result = await self._processors.retention_policy.update.run(
            UpdateRetentionPolicyAction(updater=updater)
        )
        return UpdateRetentionPolicyPayload(policy=self._data_to_node(result.data))

    async def delete(self, policy_id: RetentionPolicyID) -> DeleteRetentionPolicyPayload:
        result = await self._processors.retention_policy.delete.run(
            DeleteRetentionPolicyAction(id=policy_id)
        )
        return DeleteRetentionPolicyPayload(id=result.data.id)

    async def purge(self, policy_id: RetentionPolicyID) -> PurgeRetentionPolicyPayload:
        purger = RetentionPolicyPurger(policy_id=policy_id)
        result = await self._processors.retention_policy.purge.run(
            PurgeRetentionPolicyAction(purger=purger)
        )
        return PurgeRetentionPolicyPayload(id=result.data.id)

    def _convert_filter(self, filter_: RetentionPolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.category is not None:
            conditions.append(RetentionPolicyConditions.by_category_equals(filter_.category))
        if filter_.enabled is not None:
            conditions.append(RetentionPolicyConditions.by_enabled(filter_.enabled))
        return conditions

    def _convert_orders(self, orders: list[RetentionPolicyOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case RetentionPolicyOrderField.CATEGORY:
                    result.append(RetentionPolicyOrders.category(ascending))
                case RetentionPolicyOrderField.CREATED_AT:
                    result.append(RetentionPolicyOrders.created_at(ascending))
                case RetentionPolicyOrderField.LAST_SWEPT_AT:
                    result.append(RetentionPolicyOrders.last_swept_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: RetentionPolicyData) -> RetentionPolicyNode:
        return RetentionPolicyNode(
            id=data.id,
            category=data.category,
            retention_period_days=data.retention_period.days,
            enabled=data.enabled,
            last_swept_at=data.last_swept_at,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
