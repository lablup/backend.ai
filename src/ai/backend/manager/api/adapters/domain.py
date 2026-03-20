"""Domain adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
    DomainOrder,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AdminSearchDomainsPayload,
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainRegistryInfo,
)
from ai.backend.common.dto.manager.v2.domain.types import DomainOrderField, OrderDirection
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.domain.orders import DomainOrders
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.domain.types import DomainSearchScope
from ai.backend.manager.services.domain.actions.get_domain import GetDomainAction
from ai.backend.manager.services.domain.actions.search_domains import SearchDomainsAction
from ai.backend.manager.services.domain.actions.search_rg_domains import SearchRGDomainsAction

from .base import BaseAdapter

_DOMAIN_PAGINATION_SPEC = PaginationSpec(
    forward_order=DomainOrders.created_at(ascending=False),
    backward_order=DomainOrders.created_at(ascending=True),
    forward_condition_factory=DomainConditions.by_cursor_forward,
    backward_condition_factory=DomainConditions.by_cursor_backward,
    tiebreaker_order=DomainRow.name.asc(),
)


class DomainAdapter(BaseAdapter):
    """Adapter for domain operations."""

    async def batch_load_by_names(self, names: Sequence[str]) -> list[DomainNode | None]:
        """Batch load domains by name for DataLoader use.

        Returns DomainNode DTOs in the same order as the input names list.
        """
        if not names:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[DomainConditions.by_names(names)],
        )
        action_result = await self._processors.domain.search_domains.wait_for_complete(
            SearchDomainsAction(querier=querier)
        )
        domain_map = {data.name: self._domain_data_to_node(data) for data in action_result.items}
        return [domain_map.get(name) for name in names]

    async def get(self, domain_name: str) -> DomainNode:
        """Retrieve a single domain by name."""
        action_result = await self._processors.domain.get_domain.wait_for_complete(
            GetDomainAction(domain_name=domain_name)
        )
        return self._domain_data_to_node(action_result.data)

    async def admin_search(
        self,
        input: AdminSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search domains (admin, no scope) with filters, orders, and pagination."""
        conditions = self._convert_domain_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_DOMAIN_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        action_result = await self._processors.domain.search_domains.wait_for_complete(
            SearchDomainsAction(querier=querier)
        )

        return AdminSearchDomainsPayload(
            items=[self._domain_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_rg_domains(
        self,
        scope: DomainSearchScope,
        input: AdminSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search domains within a resource group scope."""
        conditions = self._convert_domain_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        base_conditions: list[QueryCondition] = [scope.to_condition()]
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_DOMAIN_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=base_conditions,
        )

        action_result = await self._processors.domain.search_rg_domains.wait_for_complete(
            SearchRGDomainsAction(scope=scope, querier=querier)
        )

        return AdminSearchDomainsPayload(
            items=[self._domain_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_domain_filter(self, filter: DomainFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self._convert_name_filter(filter.name)
            if condition is not None:
                conditions.append(condition)

        if filter.description is not None:
            condition = self._convert_description_filter(filter.description)
            if condition is not None:
                conditions.append(condition)

        if filter.is_active is not None:
            conditions.append(DomainConditions.by_is_active(filter.is_active))

        if filter.created_at is not None:
            condition = filter.created_at.build_query_condition(
                before_factory=DomainConditions.by_created_at_before,
                after_factory=DomainConditions.by_created_at_after,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.modified_at is not None:
            condition = filter.modified_at.build_query_condition(
                before_factory=DomainConditions.by_modified_at_before,
                after_factory=DomainConditions.by_modified_at_after,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.project is not None:
            if filter.project.name is not None:
                condition = filter.project.name.build_query_condition(
                    contains_factory=DomainConditions.by_project_name_contains,
                    equals_factory=DomainConditions.by_project_name_equals,
                    starts_with_factory=DomainConditions.by_project_name_starts_with,
                    ends_with_factory=DomainConditions.by_project_name_ends_with,
                )
                if condition is not None:
                    conditions.append(condition)
            if filter.project.is_active is not None:
                conditions.append(DomainConditions.by_project_is_active(filter.project.is_active))

        if filter.user is not None:
            if filter.user.username is not None:
                condition = filter.user.username.build_query_condition(
                    contains_factory=DomainConditions.by_user_username_contains,
                    equals_factory=DomainConditions.by_user_username_equals,
                    starts_with_factory=DomainConditions.by_user_username_starts_with,
                    ends_with_factory=DomainConditions.by_user_username_ends_with,
                )
                if condition is not None:
                    conditions.append(condition)
            if filter.user.email is not None:
                condition = filter.user.email.build_query_condition(
                    contains_factory=DomainConditions.by_user_email_contains,
                    equals_factory=DomainConditions.by_user_email_equals,
                    starts_with_factory=DomainConditions.by_user_email_starts_with,
                    ends_with_factory=DomainConditions.by_user_email_ends_with,
                )
                if condition is not None:
                    conditions.append(condition)
            if filter.user.is_active is not None:
                conditions.append(DomainConditions.by_user_is_active(filter.user.is_active))

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_domain_filter(sub_filter))

        if filter.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_sub_conditions.extend(self._convert_domain_filter(sub_filter))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))

        if filter.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_sub_conditions.extend(self._convert_domain_filter(sub_filter))
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

        return conditions

    def _convert_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=DomainConditions.by_name_contains,
            equals_factory=DomainConditions.by_name_equals,
            starts_with_factory=DomainConditions.by_name_starts_with,
            ends_with_factory=DomainConditions.by_name_ends_with,
        )

    def _convert_description_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=DomainConditions.by_description_contains,
            equals_factory=DomainConditions.by_description_equals,
            starts_with_factory=DomainConditions.by_description_starts_with,
            ends_with_factory=DomainConditions.by_description_ends_with,
        )

    @staticmethod
    def _convert_orders(order: list[DomainOrder]) -> list[QueryOrder]:
        return [_resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _domain_data_to_node(data: DomainData) -> DomainNode:
        """Convert data layer type to Pydantic DTO."""
        return DomainNode(
            id=data.name,
            basic_info=DomainBasicInfo(
                name=data.name,
                description=data.description,
                integration_id=data.integration_id,
            ),
            registry=DomainRegistryInfo(
                allowed_docker_registries=data.allowed_docker_registries,
            ),
            lifecycle=DomainLifecycleInfo(
                is_active=data.is_active,
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )


def _resolve_order(field: DomainOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DomainOrderField + OrderDirection pair to a QueryOrder."""
    ascending = direction == OrderDirection.ASC
    match field:
        case DomainOrderField.NAME:
            return DomainOrders.name(ascending)
        case DomainOrderField.CREATED_AT:
            return DomainOrders.created_at(ascending)
        case DomainOrderField.MODIFIED_AT:
            return DomainOrders.modified_at(ascending)
        case DomainOrderField.IS_ACTIVE:
            return DomainOrders.is_active(ascending)
        case DomainOrderField.PROJECT_NAME:
            return DomainOrders.by_project_name(ascending)
        case DomainOrderField.USER_USERNAME:
            return DomainOrders.by_user_username(ascending)
        case DomainOrderField.USER_EMAIL:
            return DomainOrders.by_user_email(ascending)
