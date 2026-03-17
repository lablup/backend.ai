"""Project adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchGroupsInput,
    GroupFilter,
    GroupOrder,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AdminSearchGroupsPayload,
    ProjectBasicInfo,
    ProjectLifecycleInfo,
    ProjectNode,
    ProjectOrganizationInfo,
    ProjectStorageInfo,
    VFolderHostPermissionEntry,
)
from ai.backend.common.dto.manager.v2.group.types import (
    GroupOrderField,
    OrderDirection,
    ProjectType,
)
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.conditions import GroupConditions
from ai.backend.manager.models.group.orders import GroupOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.group.actions.search_projects import SearchProjectsAction

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class ProjectAdapter(BaseAdapter):
    """Adapter for project (group) operations."""

    async def admin_search(
        self,
        input: AdminSearchGroupsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects (admin, no scope) with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = await self._processors.group.search_projects.wait_for_complete(
            SearchProjectsAction(querier=querier)
        )

        return AdminSearchGroupsPayload(
            items=[self._group_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchGroupsInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: GroupFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self._convert_name_filter(filter.name)
            if condition is not None:
                conditions.append(condition)
        if filter.domain_name is not None:
            condition = self._convert_domain_name_filter(filter.domain_name)
            if condition is not None:
                conditions.append(condition)
        if filter.is_active is not None:
            conditions.append(GroupConditions.by_is_active(filter.is_active))
        return conditions

    def _convert_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=GroupConditions.by_name_contains,
            equals_factory=GroupConditions.by_name_equals,
            starts_with_factory=GroupConditions.by_name_starts_with,
            ends_with_factory=GroupConditions.by_name_ends_with,
        )

    def _convert_domain_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=GroupConditions.by_domain_name_contains,
            equals_factory=GroupConditions.by_domain_name_equals,
            starts_with_factory=GroupConditions.by_domain_name_starts_with,
            ends_with_factory=GroupConditions.by_domain_name_ends_with,
        )

    @staticmethod
    def _convert_orders(order: list[GroupOrder]) -> list[QueryOrder]:
        return [_resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _build_pagination(input: AdminSearchGroupsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _group_data_to_node(data: GroupData) -> ProjectNode:
        """Convert data layer type to Pydantic DTO."""
        vfolder_host_entries = [
            VFolderHostPermissionEntry(
                host=host,
                permissions=[perm.value for perm in perms],
            )
            for host, perms in data.allowed_vfolder_hosts.items()
        ]

        return ProjectNode(
            id=data.id,
            basic_info=ProjectBasicInfo(
                name=data.name,
                description=data.description,
                type=ProjectType(data.type.value),
                integration_id=data.integration_id,
            ),
            organization=ProjectOrganizationInfo(
                domain_name=data.domain_name,
                resource_policy=data.resource_policy,
            ),
            storage=ProjectStorageInfo(
                allowed_vfolder_hosts=vfolder_host_entries,
            ),
            lifecycle=ProjectLifecycleInfo(
                is_active=data.is_active,
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )


def _resolve_order(field: GroupOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a GroupOrderField + OrderDirection pair to a QueryOrder."""
    ascending = direction == OrderDirection.ASC
    match field:
        case GroupOrderField.NAME:
            return GroupOrders.name(ascending)
        case GroupOrderField.CREATED_AT:
            return GroupOrders.created_at(ascending)
        case GroupOrderField.MODIFIED_AT:
            return GroupOrders.modified_at(ascending)
