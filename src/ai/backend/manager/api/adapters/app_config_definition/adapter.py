"""App config definition adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionFilter,
    AppConfigDefinitionOrder,
    CreateAppConfigDefinitionInput,
    PurgeAppConfigDefinitionInput,
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
    CreateAppConfigDefinitionPayload,
    PurgeAppConfigDefinitionPayload,
    SearchAppConfigDefinitionsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_definition.types import (
    AppConfigDefinitionOrderField,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.conditions import (
    AppConfigDefinitionConditions,
)
from ai.backend.manager.models.app_config_definition.orders import AppConfigDefinitionOrders
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.repositories.app_config_definition.creators import (
    AppConfigDefinitionCreatorSpec,
)
from ai.backend.manager.repositories.base import Purger
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.app_config_definition.actions.create import (
    CreateAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.get import (
    GetAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.purge import (
    PurgeAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.search import (
    SearchAppConfigDefinitionsAction,
)


@lru_cache(maxsize=1)
def _get_app_config_definition_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AppConfigDefinitionOrders.created_at(ascending=False),
        backward_order=AppConfigDefinitionOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigDefinitionConditions.by_cursor_forward,
        backward_condition_factory=AppConfigDefinitionConditions.by_cursor_backward,
        tiebreaker_order=AppConfigDefinitionOrders.id(ascending=True),
    )


class AppConfigDefinitionAdapter(BaseAdapter):
    """Adapter for app config definition domain operations (admin-only)."""

    async def admin_create(
        self, input: CreateAppConfigDefinitionInput
    ) -> CreateAppConfigDefinitionPayload:
        creator = Creator(spec=AppConfigDefinitionCreatorSpec(config_name=input.config_name))
        action_result = await self._processors.app_config_definition.create.wait_for_complete(
            CreateAppConfigDefinitionAction(creator=creator)
        )
        return CreateAppConfigDefinitionPayload(
            app_config_definition=self._data_to_node(action_result.definition),
        )

    async def admin_get(self, definition_id: AppConfigDefinitionID) -> AppConfigDefinitionNode:
        action_result = await self._processors.app_config_definition.get.wait_for_complete(
            GetAppConfigDefinitionAction(definition_id=definition_id)
        )
        return self._data_to_node(action_result.definition)

    async def batch_load_by_ids(
        self, ids: Sequence[AppConfigDefinitionID]
    ) -> list[AppConfigDefinitionNode | None]:
        """Batch load app config definitions by id for DataLoader use.

        Returns nodes in the same order as the input ids, with None for missing ones.
        """
        if not ids:
            return []
        querier = self._build_querier(
            conditions=[AppConfigDefinitionConditions.by_ids(list(ids))],
            orders=[],
            pagination_spec=_get_app_config_definition_pagination_spec(),
            limit=len(ids),
        )
        action_result = await self._processors.app_config_definition.search.wait_for_complete(
            SearchAppConfigDefinitionsAction(querier=querier)
        )
        node_map = {node.id: node for node in map(self._data_to_node, action_result.data)}
        return [node_map.get(definition_id) for definition_id in ids]

    async def admin_search(
        self, input: SearchAppConfigDefinitionsInput
    ) -> SearchAppConfigDefinitionsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_app_config_definition_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.app_config_definition.search.wait_for_complete(
            SearchAppConfigDefinitionsAction(querier=querier)
        )
        return SearchAppConfigDefinitionsPayload(
            items=[self._data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_purge(
        self, input: PurgeAppConfigDefinitionInput
    ) -> PurgeAppConfigDefinitionPayload:
        purger = Purger(row_class=AppConfigDefinitionRow, pk_value=AppConfigDefinitionID(input.id))
        action_result = await self._processors.app_config_definition.purge.wait_for_complete(
            PurgeAppConfigDefinitionAction(purger=purger)
        )
        return PurgeAppConfigDefinitionPayload(id=action_result.definition.id)

    @staticmethod
    def _data_to_node(data: AppConfigDefinitionData) -> AppConfigDefinitionNode:
        return AppConfigDefinitionNode(
            id=data.id,
            config_name=data.config_name,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def _convert_filter(self, filter_: AppConfigDefinitionFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.config_name:
            condition = self.convert_string_filter(
                filter_.config_name,
                contains_factory=AppConfigDefinitionConditions.by_config_name_contains,
                equals_factory=AppConfigDefinitionConditions.by_config_name_equals,
                starts_with_factory=AppConfigDefinitionConditions.by_config_name_starts_with,
                ends_with_factory=AppConfigDefinitionConditions.by_config_name_ends_with,
                in_factory=AppConfigDefinitionConditions.by_config_name_in,
            )
            if condition:
                conditions.append(condition)
        if filter_.created_at:
            condition = filter_.created_at.build_query_condition(
                before_factory=AppConfigDefinitionConditions.by_created_at_before,
                after_factory=AppConfigDefinitionConditions.by_created_at_after,
                equals_factory=AppConfigDefinitionConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)
        if filter_.updated_at:
            condition = filter_.updated_at.build_query_condition(
                before_factory=AppConfigDefinitionConditions.by_updated_at_before,
                after_factory=AppConfigDefinitionConditions.by_updated_at_after,
                equals_factory=AppConfigDefinitionConditions.by_updated_at_equals,
            )
            if condition:
                conditions.append(condition)
        return conditions

    def _convert_orders(self, orders: list[AppConfigDefinitionOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case AppConfigDefinitionOrderField.CONFIG_NAME:
                    result.append(AppConfigDefinitionOrders.config_name(ascending))
                case AppConfigDefinitionOrderField.CREATED_AT:
                    result.append(AppConfigDefinitionOrders.created_at(ascending))
                case AppConfigDefinitionOrderField.UPDATED_AT:
                    result.append(AppConfigDefinitionOrders.updated_at(ascending))
        return result
