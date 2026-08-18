"""Domain adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
    DomainFilter,
    DomainOrder,
    PurgeDomainInput,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AdminSearchDomainsPayload,
    DeleteDomainPayload,
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainPayload,
    DomainRegistryInfo,
    PurgeDomainPayload,
)
from ai.backend.common.dto.manager.v2.domain.types import DomainOrderField, OrderDirection
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.domain.orders import DomainOrders
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.searchers import DomainSearcher
from ai.backend.manager.models.domain.updaters import DomainSoftDeleteUpdater, DomainUpdater
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.base import (
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.domain.actions.create_domain_node import CreateDomainNodeAction
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction
from ai.backend.manager.services.domain.actions.search_domains import GlobalSearchDomainsAction
from ai.backend.manager.services.domain.actions.search_rg_domains import SearchRGDomainsAction
from ai.backend.manager.services.domain.actions.update_domain_node import UpdateDomainNodeAction
from ai.backend.manager.types import OptionalState, TriState

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
        searcher = DomainSearcher(
            pagination=NoPagination(),
            conditions=[DomainConditions.by_names(names)],
        )
        result = await self._processors.domain.global_search.run(
            GlobalSearchDomainsAction(searcher=searcher)
        )
        domain_map = {data.name: self._domain_data_to_node(data) for data in result.items}
        return [domain_map.get(name) for name in names]

    async def batch_load_by_ids(self, ids: Sequence[DomainID]) -> list[DomainNode | None]:
        """Batch load domains by UUID for DataLoader use.

        Returns DomainNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        searcher = DomainSearcher(
            pagination=NoPagination(),
            conditions=[DomainConditions.by_ids(ids)],
        )
        result = await self._processors.domain.global_search.run(
            GlobalSearchDomainsAction(searcher=searcher)
        )
        domain_map = {data.id: self._domain_data_to_node(data) for data in result.items}
        return [domain_map.get(domain_id) for domain_id in ids]

    async def get(self, domain_name: str) -> DomainNode:
        """Retrieve a single domain by name."""
        result = await self._processors.domain.lookup.run(
            LookupDomainAction(name=DomainName(domain_name))
        )
        return self._domain_data_to_node(result.data)

    async def admin_search(
        self,
        input: AdminSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search domains (admin, no scope) with filters, orders, and pagination."""
        conditions = self._convert_domain_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            DomainSearcher,
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

        result = await self._processors.domain.global_search.run(
            GlobalSearchDomainsAction(searcher=searcher)
        )

        return AdminSearchDomainsPayload(
            items=[self._domain_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_rg_domains(
        self,
        resource_group_name: str,
        input: AdminSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search the domains a resource group serves."""
        conditions = self._convert_domain_filter(input.filter) if input.filter else []
        conditions.append(DomainConditions.by_resource_group_name(resource_group_name))
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            DomainSearcher,
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

        result = await self._processors.domain.public_search_rg_domains.run(
            SearchRGDomainsAction(searcher=searcher)
        )

        return AdminSearchDomainsPayload(
            items=[self._domain_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def admin_create(
        self,
        input: CreateDomainInput,
        user_info: UserInfo,
    ) -> DomainPayload:
        """Create a new domain (superadmin only)."""
        result = await self._processors.domain.create_domain_node.run(
            CreateDomainNodeAction(
                user_info=user_info,
                creator=DomainCreator(
                    name=input.name,
                    description=input.description,
                    is_active=input.is_active,
                    allowed_docker_registries=input.allowed_docker_registries,
                    integration_name=input.integration_name,
                ),
            )
        )
        return DomainPayload(domain=self._domain_data_to_node(result.domain_data))

    async def admin_update(
        self,
        domain_name: str,
        input: UpdateDomainInput,
        user_info: UserInfo,
    ) -> DomainPayload:
        """Update an existing domain (superadmin only)."""
        target = await self._processors.domain.lookup.run(
            LookupDomainAction(name=DomainName(domain_name))
        )
        updater = DomainUpdater(
            name=domain_name,
            description=(
                TriState.nop()
                if isinstance(input.description, Sentinel)
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
            is_active=(
                OptionalState.update(input.is_active)
                if input.is_active is not None
                else OptionalState.nop()
            ),
            allowed_docker_registries=(
                OptionalState.nop()
                if isinstance(input.allowed_docker_registries, Sentinel)
                else OptionalState.update(input.allowed_docker_registries)
                if input.allowed_docker_registries is not None
                else OptionalState.nop()
            ),
            integration_name=(
                TriState.nop()
                if isinstance(input.integration_name, Sentinel)
                else TriState.nullify()
                if input.integration_name is None
                else TriState.update(input.integration_name)
            ),
        )
        result = await self._processors.domain.update_domain_node.run(
            UpdateDomainNodeAction(
                domain_id=target.data.id,
                updater=updater,
                user_info=user_info,
            )
        )
        return DomainPayload(domain=self._domain_data_to_node(result.domain_data))

    async def admin_delete(
        self,
        input: DeleteDomainInput,
        user_info: UserInfo,
    ) -> DeleteDomainPayload:
        """Soft-delete a domain (superadmin only)."""
        target = await self._processors.domain.lookup.run(
            LookupDomainAction(name=DomainName(input.name))
        )
        await self._processors.domain.delete_domain.run(
            DeleteDomainAction(
                domain_id=target.data.id,
                updater=DomainSoftDeleteUpdater(name=input.name),
            )
        )
        return DeleteDomainPayload(deleted=True)

    async def admin_purge(
        self,
        input: PurgeDomainInput,
        user_info: UserInfo,
    ) -> PurgeDomainPayload:
        """Permanently purge a domain (superadmin only)."""
        target = await self._processors.domain.lookup.run(
            LookupDomainAction(name=DomainName(input.name))
        )
        await self._processors.domain.purge_domain.run(
            PurgeDomainAction(domain_id=target.data.id, name=input.name)
        )
        return PurgeDomainPayload(purged=True)

    def _convert_domain_filter(self, filter: DomainFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self._convert_name_filter(filter.name)
            if condition is not None:
                conditions.append(condition)

        if filter.id is not None:
            condition = filter.id.build_query_condition(
                equals_factory=DomainConditions.by_id_equals,
                in_factory=DomainConditions.by_id_in,
            )
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
                equals_factory=DomainConditions.by_created_at_equals,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.modified_at is not None:
            condition = filter.modified_at.build_query_condition(
                before_factory=DomainConditions.by_updated_at_before,
                after_factory=DomainConditions.by_updated_at_after,
                equals_factory=DomainConditions.by_updated_at_equals,
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
                    in_factory=DomainConditions.by_project_name_in,
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
                    in_factory=DomainConditions.by_user_username_in,
                )
                if condition is not None:
                    conditions.append(condition)
            if filter.user.email is not None:
                condition = filter.user.email.build_query_condition(
                    contains_factory=DomainConditions.by_user_email_contains,
                    equals_factory=DomainConditions.by_user_email_equals,
                    starts_with_factory=DomainConditions.by_user_email_starts_with,
                    ends_with_factory=DomainConditions.by_user_email_ends_with,
                    in_factory=DomainConditions.by_user_email_in,
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
            in_factory=DomainConditions.by_name_in,
        )

    def _convert_description_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=DomainConditions.by_description_contains,
            equals_factory=DomainConditions.by_description_equals,
            starts_with_factory=DomainConditions.by_description_starts_with,
            ends_with_factory=DomainConditions.by_description_ends_with,
            in_factory=DomainConditions.by_description_in,
        )

    @staticmethod
    def _convert_orders(order: list[DomainOrder]) -> list[QueryOrder]:
        return [_resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _domain_data_to_node(data: DomainData) -> DomainNode:
        """Convert data layer type to Pydantic DTO."""
        return DomainNode(
            id=data.id,
            basic_info=DomainBasicInfo(
                name=data.name,
                description=data.description,
                integration_name=data.integration_name,
            ),
            registry=DomainRegistryInfo(
                allowed_docker_registries=data.allowed_docker_registries,
            ),
            lifecycle=DomainLifecycleInfo(
                is_active=data.is_active,
                is_default=data.is_default,
                created_at=data.created_at,
                modified_at=data.updated_at,
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
            return DomainOrders.updated_at(ascending)
        case DomainOrderField.IS_ACTIVE:
            return DomainOrders.is_active(ascending)
        case DomainOrderField.PROJECT_NAME:
            return DomainOrders.by_project_name(ascending)
        case DomainOrderField.USER_USERNAME:
            return DomainOrders.by_user_username(ascending)
        case DomainOrderField.USER_EMAIL:
            return DomainOrders.by_user_email(ascending)
