"""AppConfigPolicy domain adapter — Pydantic-in / Pydantic-out transport layer."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AppConfigPolicyFilter,
    AppConfigPolicyOrder,
    CreateAppConfigPolicyInput,
    PurgeAppConfigPolicyInput,
    SearchAppConfigPoliciesInput,
    UpdateAppConfigPolicyInput,
)
from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AppConfigPolicyNode,
    CreateAppConfigPolicyPayload,
    GetAppConfigPolicyPayload,
    PurgeAppConfigPolicyPayload,
    SearchAppConfigPoliciesPayload,
    UpdateAppConfigPolicyPayload,
)
from ai.backend.common.dto.manager.v2.app_config_policy.types import OrderDirection
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.app_config_policy.conditions import AppConfigPolicyConditions
from ai.backend.manager.models.app_config_policy.orders import AppConfigPolicyOrders
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.base import BatchQuerier, QueryCondition, QueryOrder
from ai.backend.manager.services.app_config_policy.actions.create import (
    CreateAppConfigPolicyAction,
)
from ai.backend.manager.services.app_config_policy.actions.get import GetAppConfigPolicyAction
from ai.backend.manager.services.app_config_policy.actions.purge import (
    PurgeAppConfigPolicyAction,
)
from ai.backend.manager.services.app_config_policy.actions.search import (
    SearchAppConfigPoliciesAction,
)
from ai.backend.manager.services.app_config_policy.actions.update import (
    UpdateAppConfigPolicyAction,
)

from .base import BaseAdapter
from .pagination import PaginationSpec


class AppConfigPolicyAdapter(BaseAdapter):
    """Adapter for AppConfigPolicy domain operations (BEP-1052 §1)."""

    async def create(self, input: CreateAppConfigPolicyInput) -> CreateAppConfigPolicyPayload:
        result = await self._processors.app_config_policy.create.wait_for_complete(
            CreateAppConfigPolicyAction(
                config_name=input.config_name,
                scope_sources=list(input.scope_sources),
            )
        )
        return CreateAppConfigPolicyPayload(item=self._data_to_dto(result.policy))

    async def get(self, config_name: str) -> GetAppConfigPolicyPayload:
        result = await self._processors.app_config_policy.get.wait_for_complete(
            GetAppConfigPolicyAction(config_name=config_name)
        )
        return GetAppConfigPolicyPayload(
            item=self._data_to_dto(result.policy) if result.policy is not None else None,
        )

    async def search(self, input: SearchAppConfigPoliciesInput) -> SearchAppConfigPoliciesPayload:
        querier = self._build_querier_from_input(input)
        result = await self._processors.app_config_policy.search.wait_for_complete(
            SearchAppConfigPoliciesAction(querier=querier)
        )
        return SearchAppConfigPoliciesPayload(
            items=[self._data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update(self, input: UpdateAppConfigPolicyInput) -> UpdateAppConfigPolicyPayload:
        result = await self._processors.app_config_policy.update.wait_for_complete(
            UpdateAppConfigPolicyAction(
                config_name=input.config_name,
                scope_sources=list(input.scope_sources),
            )
        )
        # Service raises ObjectNotFound when the config_name does not exist,
        # so `result.policy` is guaranteed to be non-None here.
        if result.policy is None:
            raise ObjectNotFound(object_name=f"AppConfigPolicy({input.config_name})")
        return UpdateAppConfigPolicyPayload(item=self._data_to_dto(result.policy))

    async def purge(self, input: PurgeAppConfigPolicyInput) -> PurgeAppConfigPolicyPayload:
        result = await self._processors.app_config_policy.purge.wait_for_complete(
            PurgeAppConfigPolicyAction(config_name=input.config_name)
        )
        return PurgeAppConfigPolicyPayload(
            config_name=result.config_name,
            purged=result.purged,
        )

    _PAGINATION_SPEC = PaginationSpec(
        forward_order=AppConfigPolicyOrders.created_at(ascending=False),
        backward_order=AppConfigPolicyOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigPolicyConditions.by_cursor_forward,
        backward_condition_factory=AppConfigPolicyConditions.by_cursor_backward,
        tiebreaker_order=AppConfigPolicyRow.id.asc(),
    )

    def _build_querier_from_input(self, input: SearchAppConfigPoliciesInput) -> BatchQuerier:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        return self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=self._PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _convert_filter(self, filter: AppConfigPolicyFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.config_name is not None:
            condition = self.convert_string_filter(
                filter.config_name,
                contains_factory=AppConfigPolicyConditions.by_config_name_contains,
                equals_factory=AppConfigPolicyConditions.by_config_name_equals,
                starts_with_factory=AppConfigPolicyConditions.by_config_name_starts_with,
                ends_with_factory=AppConfigPolicyConditions.by_config_name_ends_with,
                in_factory=AppConfigPolicyConditions.by_config_name_in,
            )
            if condition is not None:
                conditions.append(condition)
        return conditions

    @staticmethod
    def _convert_orders(orders: list[AppConfigPolicyOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field.value:
                case "config_name":
                    result.append(AppConfigPolicyOrders.config_name(ascending))
                case "created_at":
                    result.append(AppConfigPolicyOrders.created_at(ascending))
        return result

    @staticmethod
    def _data_to_dto(data: AppConfigPolicyData) -> AppConfigPolicyNode:
        return AppConfigPolicyNode(
            id=data.id,
            config_name=data.config_name,
            scope_sources=list(data.scope_sources),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
