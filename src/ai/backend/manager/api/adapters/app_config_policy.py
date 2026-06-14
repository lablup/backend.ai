"""AppConfigPolicy domain adapter — Pydantic-in / Pydantic-out transport layer."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminBulkCreateAppConfigPoliciesInput,
    AdminBulkPurgeAppConfigPoliciesInput,
    AdminBulkUpdateAppConfigPoliciesInput,
    AdminSearchAppConfigPoliciesInput,
    AppConfigPolicyFilter,
    AppConfigPolicyOrder,
    ScopedSearchAppConfigPoliciesInput,
)
from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AdminBulkCreateAppConfigPoliciesPayload,
    AdminBulkPurgeAppConfigPoliciesPayload,
    AdminBulkUpdateAppConfigPoliciesPayload,
    AppConfigPolicyBulkError,
    AppConfigPolicyNode,
    GetAppConfigPolicyPayload,
    SearchAppConfigPoliciesPayload,
)
from ai.backend.common.dto.manager.v2.app_config_policy.types import (
    AppConfigPolicyOrderField,
    OrderDirection,
)
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.data.app_config_policy.types import (
    AppConfigPolicyBulkCreateItem,
    AppConfigPolicyBulkItemError,
    AppConfigPolicyBulkUpdateItem,
    AppConfigPolicyData,
)
from ai.backend.manager.models.app_config_policy.conditions import AppConfigPolicyConditions
from ai.backend.manager.models.app_config_policy.orders import AppConfigPolicyOrders
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.base import BatchQuerier, QueryCondition, QueryOrder
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_create import (
    AdminBulkCreateAppConfigPoliciesAction,
)
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_purge import (
    AdminBulkPurgeAppConfigPoliciesAction,
)
from ai.backend.manager.services.app_config_policy.actions.admin_bulk_update import (
    AdminBulkUpdateAppConfigPoliciesAction,
)
from ai.backend.manager.services.app_config_policy.actions.admin_search import (
    AdminSearchAppConfigPoliciesAction,
)
from ai.backend.manager.services.app_config_policy.actions.get import GetAppConfigPolicyAction
from ai.backend.manager.services.app_config_policy.actions.scoped_search import (
    ConfigNameAppConfigPolicyTarget,
    ScopedSearchAppConfigPoliciesAction,
)

from .base import BaseAdapter


class AppConfigPolicyAdapter(BaseAdapter):
    """Adapter for AppConfigPolicy domain operations.

    Writes are bulk-only; single-item create / update / purge entry
    points are intentionally absent.
    """

    # ── Public surface ─────────────────────────────────────────────

    async def get(self, id: AppConfigPolicyID) -> GetAppConfigPolicyPayload:
        result = await self._processors.app_config_policy.get.wait_for_complete(
            GetAppConfigPolicyAction(id=id)
        )
        return GetAppConfigPolicyPayload(
            item=self._data_to_dto(result.policy),
        )

    async def admin_search(
        self, input: AdminSearchAppConfigPoliciesInput
    ) -> SearchAppConfigPoliciesPayload:
        querier = self._build_querier_from_input(input)
        result = await self._processors.app_config_policy.admin_search.wait_for_complete(
            AdminSearchAppConfigPoliciesAction(querier=querier)
        )
        return SearchAppConfigPoliciesPayload(
            items=[self._data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search(
        self, input: ScopedSearchAppConfigPoliciesInput
    ) -> SearchAppConfigPoliciesPayload:
        querier = self._build_querier_from_input(input)
        targets: list[SearchableActionTarget] = [
            ConfigNameAppConfigPolicyTarget(config_name=config_name)
            for config_name in input.scope.config_names
        ]
        result = await self._processors.app_config_policy.scoped_search.wait_for_complete(
            ScopedSearchAppConfigPoliciesAction(items=targets, querier=querier)
        )
        return SearchAppConfigPoliciesPayload(
            items=[self._data_to_dto(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_bulk_create(
        self, input: AdminBulkCreateAppConfigPoliciesInput
    ) -> AdminBulkCreateAppConfigPoliciesPayload:
        items = [
            AppConfigPolicyBulkCreateItem(
                config_name=item.config_name,
                scope_sources=list(item.scope_sources),
            )
            for item in input.items
        ]
        result = await self._processors.app_config_policy.admin_bulk_create.wait_for_complete(
            AdminBulkCreateAppConfigPoliciesAction(items=items)
        )
        return AdminBulkCreateAppConfigPoliciesPayload(
            created=[self._data_to_dto(policy) for policy in result.created],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    async def admin_bulk_update(
        self, input: AdminBulkUpdateAppConfigPoliciesInput
    ) -> AdminBulkUpdateAppConfigPoliciesPayload:
        items = [
            AppConfigPolicyBulkUpdateItem(
                id=item.id,
                scope_sources=list(item.scope_sources),
            )
            for item in input.items
        ]
        result = await self._processors.app_config_policy.admin_bulk_update.wait_for_complete(
            AdminBulkUpdateAppConfigPoliciesAction(items=items)
        )
        return AdminBulkUpdateAppConfigPoliciesPayload(
            updated=[self._data_to_dto(policy) for policy in result.updated],
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    async def admin_bulk_purge(
        self, input: AdminBulkPurgeAppConfigPoliciesInput
    ) -> AdminBulkPurgeAppConfigPoliciesPayload:
        result = await self._processors.app_config_policy.admin_bulk_purge.wait_for_complete(
            AdminBulkPurgeAppConfigPoliciesAction(ids=list(input.ids))
        )
        return AdminBulkPurgeAppConfigPoliciesPayload(
            purged_ids=list(result.purged_ids),
            failed=[self._bulk_error_to_dto(err) for err in result.failed],
        )

    # ── Private helpers ────────────────────────────────────────────

    _PAGINATION_SPEC = PaginationSpec(
        forward_order=AppConfigPolicyOrders.created_at(ascending=False),
        backward_order=AppConfigPolicyOrders.created_at(ascending=True),
        forward_condition_factory=AppConfigPolicyConditions.by_cursor_forward,
        backward_condition_factory=AppConfigPolicyConditions.by_cursor_backward,
        tiebreaker_order=AppConfigPolicyRow.id.asc(),
    )

    def _build_querier_from_input(
        self,
        input: AdminSearchAppConfigPoliciesInput | ScopedSearchAppConfigPoliciesInput,
    ) -> BatchQuerier:
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
        if filter.created_at is not None:
            condition = filter.created_at.build_query_condition(
                before_factory=AppConfigPolicyConditions.by_created_at_before,
                after_factory=AppConfigPolicyConditions.by_created_at_after,
                equals_factory=AppConfigPolicyConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        if filter.updated_at is not None:
            condition = filter.updated_at.build_query_condition(
                before_factory=AppConfigPolicyConditions.by_updated_at_before,
                after_factory=AppConfigPolicyConditions.by_updated_at_after,
                equals_factory=AppConfigPolicyConditions.by_updated_at_equals,
            )
            if condition is not None:
                conditions.append(condition)
        return conditions

    @staticmethod
    def _convert_orders(orders: list[AppConfigPolicyOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case AppConfigPolicyOrderField.CONFIG_NAME:
                    result.append(AppConfigPolicyOrders.config_name(ascending))
                case AppConfigPolicyOrderField.CREATED_AT:
                    result.append(AppConfigPolicyOrders.created_at(ascending))
                case AppConfigPolicyOrderField.UPDATED_AT:
                    result.append(AppConfigPolicyOrders.updated_at(ascending))
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

    @staticmethod
    def _bulk_error_to_dto(err: AppConfigPolicyBulkItemError) -> AppConfigPolicyBulkError:
        return AppConfigPolicyBulkError(
            index=err.index,
            message=err.message,
        )
