"""Domain adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
    DomainFilter,
    DomainOrder,
    PurgeDomainInput,
    RestoreDomainInput,
    ScopedSearchDomainsInput,
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
    RestoreDomainPayload,
)
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainOrderField,
    DomainProjectFilter,
    DomainUserFilter,
    OrderDirection,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.domain.deprecated_search import (
    DeprecatedDomainConditions,
    DeprecatedDomainOrders,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.scopes import (
    ResourceGroupDomainTarget,
)
from ai.backend.manager.models.domain.searchable_fields import DomainSearchableFields
from ai.backend.manager.models.domain.searchers import DomainSearcher
from ai.backend.manager.models.domain.updaters import (
    DomainRestoreUpdater,
    DomainSoftDeleteUpdater,
    DomainUpdater,
)
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.services.domain.actions.bulk_get import BulkGetDomainsAction
from ai.backend.manager.services.domain.actions.bulk_lookup import BulkLookupDomainsAction
from ai.backend.manager.services.domain.actions.create_domain_node import CreateDomainNodeAction
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.get import GetDomainAction
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.actions.purge_domain import PurgeDomainAction
from ai.backend.manager.services.domain.actions.restore_domain import RestoreDomainAction
from ai.backend.manager.services.domain.actions.scoped_search import (
    ScopedSearchDomainsAction,
)
from ai.backend.manager.services.domain.actions.search_domains import GlobalSearchDomainsAction
from ai.backend.manager.services.domain.actions.update_domain_node import UpdateDomainNodeAction
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.resource_group.actions.lookup import LookupResourceGroupAction
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.types import OptionalState, TriState

_DOMAIN_PAGINATION_SPEC = PaginationSpec(
    forward_order=DomainSearchableFields.own.created_at.order.apply(ascending=False),
    cursor_column=DomainRow.id,
)


class DomainAdapter(BaseAdapter):
    """Adapter for domain operations."""

    _domain: DomainProcessors
    _resource_group: ResourceGroupProcessors

    def __init__(self, domain: DomainProcessors, resource_group: ResourceGroupProcessors) -> None:
        self._domain = domain
        self._resource_group = resource_group

    async def batch_load_by_names(
        self, names: Sequence[str]
    ) -> list[DomainNode | Exception | None]:
        """Batch load domains by name for DataLoader use.

        One answer per name in the given order: the node, ``None`` for a name matching
        no domain.
        """
        if not names:
            return []
        keys = [DomainName(name) for name in names]
        lookup = await self._domain.bulk_lookup.run(BulkLookupDomainsAction(names=keys))
        ids = [lookup.resolved[key] for key in keys if key in lookup.resolved]
        got = await self._domain.bulk_get.run(BulkGetDomainsAction(ids=ids))
        domains = got.values()
        errors = got.errors()
        nodes: list[DomainNode | Exception | None] = []
        for key in keys:
            domain_id = lookup.resolved.get(key)
            if domain_id is None:
                nodes.append(None)
                continue
            data = domains.get(domain_id)
            if data is None:
                nodes.append(self.batch_load_failure(errors.get(domain_id)))
                continue
            nodes.append(self._domain_data_to_node(data))
        return nodes

    async def batch_load_by_ids(
        self, ids: Sequence[DomainID]
    ) -> list[DomainNode | Exception | None]:
        """Batch load domains by UUID for DataLoader use."""
        if not ids:
            return []
        result = await self._domain.bulk_get.run(BulkGetDomainsAction(ids=list(ids)))
        return [
            self._domain_data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def get(self, domain_name: str) -> DomainNode:
        """Retrieve a single domain by name."""
        resolved = await self._domain.lookup.run(LookupDomainAction(name=DomainName(domain_name)))
        result = await self._domain.get.run(GetDomainAction(domain_id=resolved.entity_id()))
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

        result = await self._domain.global_search.run(
            GlobalSearchDomainsAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )

        return AdminSearchDomainsPayload(
            items=[self._domain_data_to_node(item) for item in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search(
        self,
        input: ScopedSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search the domains the named scopes reach, combined with OR."""
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
        result = await self._domain.scoped_search.run(
            ScopedSearchDomainsAction(
                searcher=ScopedSearcher(
                    scopes=[
                        ResourceGroupDomainTarget(resource_group_id=ResourceGroupID(entry.value))
                        for entry in input.scope.resource_group or ()
                    ],
                    used_by=(),
                    searcher=searcher,
                )
            )
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
        resource_group = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(resource_group_name))
        )
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

        result = await self._domain.scoped_search.run(
            ScopedSearchDomainsAction(
                searcher=ScopedSearcher(
                    scopes=[
                        ResourceGroupDomainTarget(resource_group_id=resource_group.entity_id())
                    ],
                    used_by=(),
                    searcher=searcher,
                )
            )
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
        result = await self._domain.create_domain_node.run(
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
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(domain_name)))
        updater = DomainUpdater(
            domain_id=target.entity_id(),
            description=TriState.from_unset(input.description),
            is_active=OptionalState.from_unset(input.is_active),
            allowed_docker_registries=OptionalState.from_unset(input.allowed_docker_registries),
            integration_name=TriState.from_unset(input.integration_name),
        )
        result = await self._domain.update_domain_node.run(
            UpdateDomainNodeAction(
                updater=updater,
                user_info=user_info,
            )
        )
        return DomainPayload(domain=self._domain_data_to_node(result.domain_data))

    async def admin_delete(self, input: DeleteDomainInput) -> DeleteDomainPayload:
        """Soft-delete a domain (superadmin only)."""
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(input.name)))
        await self._domain.delete_domain.run(
            DeleteDomainAction(
                updater=DomainSoftDeleteUpdater(domain_id=target.entity_id()),
            )
        )
        return DeleteDomainPayload(deleted=True)

    async def admin_restore(self, input: RestoreDomainInput) -> RestoreDomainPayload:
        """Restore a soft-deleted domain (superadmin only)."""
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(input.name)))
        await self._domain.restore_domain.run(
            RestoreDomainAction(
                updater=DomainRestoreUpdater(domain_id=target.entity_id()),
            )
        )
        return RestoreDomainPayload(restored=True)

    async def admin_purge(self, input: PurgeDomainInput) -> PurgeDomainPayload:
        """Permanently purge a domain (superadmin only)."""
        target = await self._domain.lookup.run(LookupDomainAction(name=DomainName(input.name)))
        await self._domain.purge_domain.run(
            PurgeDomainAction(domain_id=target.entity_id(), name=input.name)
        )
        return PurgeDomainPayload(purged=True)

    def _convert_domain_filter(self, filter: DomainFilter) -> list[QueryCondition]:
        fields = DomainSearchableFields.own
        conditions = [
            *self.apply_string_filter(filter.name, fields.name.filter),
            *self.apply_uuid_filter(filter.id, fields.id.filter),
            *self.apply_string_filter(filter.description, fields.description.filter),
            *self.apply_bool_filter(filter.is_active, fields.is_active.filter),
            *self.apply_datetime_filter(filter.created_at, fields.created_at.filter),
            *self.apply_datetime_filter(filter.modified_at, fields.updated_at.filter),
            *self._convert_project_nested_filter(filter.project),
            *self._convert_user_nested_filter(filter.user),
        ]

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

    def _convert_project_nested_filter(
        self, project_filter: DomainProjectFilter | None
    ) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over one project of the domain."""
        if project_filter is None:
            return []
        fields = ProjectSearchableFields.own
        conditions = [
            *self.apply_string_filter(project_filter.name, fields.name.filter),
            *self.apply_bool_filter(project_filter.is_active, fields.is_active.filter),
        ]
        if not conditions:
            return []
        return [DeprecatedDomainConditions.exists_project_combined(conditions)]

    def _convert_user_nested_filter(
        self, user_filter: DomainUserFilter | None
    ) -> list[QueryCondition]:
        """Deprecated. Every condition lands in one EXISTS over one user of the domain."""
        if user_filter is None:
            return []
        fields = UserSearchableFields.own
        conditions = [
            *self.apply_string_filter(user_filter.username, fields.username.filter),
            *self.apply_string_filter(user_filter.email, fields.email.filter),
            *self._convert_member_active_filter(user_filter.is_active),
        ]
        if not conditions:
            return []
        return [DeprecatedDomainConditions.exists_user_combined(conditions)]

    def _convert_member_active_filter(self, is_active: bool | None) -> list[QueryCondition]:
        """Active means the user's account status is ACTIVE."""
        if is_active is None:
            return []
        status = UserSearchableFields.own.status.filter
        if is_active:
            return [status.equals(UserStatus.ACTIVE)]
        return [status.not_equals(UserStatus.ACTIVE)]

    def _convert_orders(self, order: list[DomainOrder]) -> list[QueryOrder]:
        return [self._convert_order(o) for o in order]

    def _convert_order(self, order: DomainOrder) -> QueryOrder:
        """The query order one requested order field names."""
        fields = DomainSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case DomainOrderField.NAME:
                return fields.name.order.apply(ascending)
            case DomainOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case DomainOrderField.MODIFIED_AT:
                return fields.updated_at.order.apply(ascending)
            case DomainOrderField.IS_ACTIVE:
                return fields.is_active.order.apply(ascending)
            case DomainOrderField.PROJECT_NAME:
                return DeprecatedDomainOrders.by_project_name(ascending)
            case DomainOrderField.USER_USERNAME:
                return DeprecatedDomainOrders.by_user_username(ascending)
            case DomainOrderField.USER_EMAIL:
                return DeprecatedDomainOrders.by_user_email(ascending)
            case _:
                assert_never(order.field)

    @staticmethod
    def _domain_data_to_node(data: DomainData) -> DomainNode:
        """Convert data layer type to Pydantic DTO."""
        return DomainNode(
            id=data.id,
            entity_id=data.entity_id(),
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
