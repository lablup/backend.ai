"""App config allow-list adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    AppConfigAllowListFilter,
    AppConfigAllowListOrder,
    CreateAppConfigAllowListInput,
    PurgeAppConfigAllowListInput,
    SearchAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
    CreateAppConfigAllowListPayload,
    PurgeAppConfigAllowListPayload,
    SearchAppConfigAllowListPayload,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigAllowListOrderField,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigScopeType as AppConfigScopeTypeDTO,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
    AppConfigScopeType,
)
from ai.backend.manager.models.app_config_allow_list.conditions import (
    AppConfigAllowListConditions,
)
from ai.backend.manager.models.app_config_allow_list.orders import AppConfigAllowListOrders
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.app_config_allow_list.creators import (
    AppConfigAllowListCreatorSpec,
)
from ai.backend.manager.repositories.base import (
    Purger,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.app_config_allow_list.actions.create import (
    CreateAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.get import (
    GetAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.purge import (
    PurgeAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.search import (
    SearchAppConfigAllowListAction,
)


@lru_cache(maxsize=1)
def _get_app_config_allow_list_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AppConfigAllowListOrders.created_at(ascending=False),
        backward_order=AppConfigAllowListOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigAllowListConditions.by_cursor_forward,
        backward_condition_factory=AppConfigAllowListConditions.by_cursor_backward,
        tiebreaker_order=AppConfigAllowListOrders.id(ascending=True),
    )


class AppConfigAllowListAdapter(BaseAdapter):
    """Adapter for app config allow-list domain operations (admin-only)."""

    async def admin_create(
        self, input: CreateAppConfigAllowListInput
    ) -> CreateAppConfigAllowListPayload:
        creator = Creator(
            spec=AppConfigAllowListCreatorSpec(
                config_name=input.config_name,
                scope_type=AppConfigScopeType(input.scope_type.value),
            )
        )
        action_result = await self._processors.app_config_allow_list.create.wait_for_complete(
            CreateAppConfigAllowListAction(creator=creator)
        )
        return CreateAppConfigAllowListPayload(
            app_config_allow_list=self._data_to_node(action_result.allow_list),
        )

    async def admin_get(self, allow_list_id: AppConfigAllowListID) -> AppConfigAllowListNode:
        action_result = await self._processors.app_config_allow_list.get.wait_for_complete(
            GetAppConfigAllowListAction(allow_list_id=allow_list_id)
        )
        return self._data_to_node(action_result.allow_list)

    async def batch_load_by_ids(
        self, ids: Sequence[AppConfigAllowListID]
    ) -> list[AppConfigAllowListNode | None]:
        """Batch load app config allow-list entries by id for DataLoader use.

        Returns nodes in the same order as the input ids, with None for missing ones.
        """
        if not ids:
            return []
        querier = self._build_querier(
            conditions=[AppConfigAllowListConditions.by_ids(list(ids))],
            orders=[],
            pagination_spec=_get_app_config_allow_list_pagination_spec(),
            limit=len(ids),
        )
        action_result = await self._processors.app_config_allow_list.search.wait_for_complete(
            SearchAppConfigAllowListAction(querier=querier)
        )
        node_map = {node.id: node for node in map(self._data_to_node, action_result.data)}
        return [node_map.get(allow_list_id) for allow_list_id in ids]

    async def admin_search(
        self, input: SearchAppConfigAllowListInput
    ) -> SearchAppConfigAllowListPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_app_config_allow_list_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.app_config_allow_list.search.wait_for_complete(
            SearchAppConfigAllowListAction(querier=querier)
        )
        return SearchAppConfigAllowListPayload(
            items=[self._data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_purge(
        self, input: PurgeAppConfigAllowListInput
    ) -> PurgeAppConfigAllowListPayload:
        purger = Purger(row_class=AppConfigAllowListRow, pk_value=AppConfigAllowListID(input.id))
        action_result = await self._processors.app_config_allow_list.purge.wait_for_complete(
            PurgeAppConfigAllowListAction(purger=purger)
        )
        return PurgeAppConfigAllowListPayload(id=action_result.allow_list.id)

    @staticmethod
    def _data_to_node(data: AppConfigAllowListData) -> AppConfigAllowListNode:
        return AppConfigAllowListNode(
            id=data.id,
            config_name=data.config_name,
            scope_type=AppConfigScopeTypeDTO(data.scope_type.value),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def _convert_filter(self, filter_: AppConfigAllowListFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.config_name:
            condition = self.convert_string_filter(
                filter_.config_name,
                contains_factory=AppConfigAllowListConditions.by_config_name_contains,
                equals_factory=AppConfigAllowListConditions.by_config_name_equals,
                starts_with_factory=AppConfigAllowListConditions.by_config_name_starts_with,
                ends_with_factory=AppConfigAllowListConditions.by_config_name_ends_with,
                in_factory=AppConfigAllowListConditions.by_config_name_in,
            )
            if condition:
                conditions.append(condition)
        if filter_.scope_type:
            conditions.extend(self._convert_scope_type_filter(filter_.scope_type))
        if filter_.created_at:
            condition = filter_.created_at.build_query_condition(
                before_factory=AppConfigAllowListConditions.by_created_at_before,
                after_factory=AppConfigAllowListConditions.by_created_at_after,
                equals_factory=AppConfigAllowListConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)
        if filter_.updated_at:
            condition = filter_.updated_at.build_query_condition(
                before_factory=AppConfigAllowListConditions.by_updated_at_before,
                after_factory=AppConfigAllowListConditions.by_updated_at_after,
                equals_factory=AppConfigAllowListConditions.by_updated_at_equals,
            )
            if condition:
                conditions.append(condition)
        return conditions

    @staticmethod
    def _convert_scope_type_filter(filter_: AppConfigScopeTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.equals is not None:
            conditions.append(
                AppConfigAllowListConditions.by_scope_type_equals(
                    AppConfigScopeType(filter_.equals.value)
                )
            )
        if filter_.in_ is not None:
            conditions.append(
                AppConfigAllowListConditions.by_scope_type_in([
                    AppConfigScopeType(value.value) for value in filter_.in_
                ])
            )
        if filter_.not_equals is not None:
            conditions.append(
                AppConfigAllowListConditions.by_scope_type_not_equals(
                    AppConfigScopeType(filter_.not_equals.value)
                )
            )
        if filter_.not_in is not None:
            conditions.append(
                AppConfigAllowListConditions.by_scope_type_not_in([
                    AppConfigScopeType(value.value) for value in filter_.not_in
                ])
            )
        return conditions

    def _convert_orders(self, orders: list[AppConfigAllowListOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case AppConfigAllowListOrderField.CONFIG_NAME:
                    result.append(AppConfigAllowListOrders.config_name(ascending))
                case AppConfigAllowListOrderField.SCOPE_TYPE:
                    result.append(AppConfigAllowListOrders.scope_type(ascending))
                case AppConfigAllowListOrderField.CREATED_AT:
                    result.append(AppConfigAllowListOrders.created_at(ascending))
                case AppConfigAllowListOrderField.UPDATED_AT:
                    result.append(AppConfigAllowListOrders.updated_at(ascending))
        return result
