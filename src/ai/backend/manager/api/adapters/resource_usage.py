"""Resource Usage adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    AdminSearchDomainUsageBucketsInput,
    AdminSearchProjectUsageBucketsInput,
    AdminSearchUserUsageBucketsInput,
    DomainSearchDomainUsageBucketsInput,
    DomainSearchProjectUsageBucketsInput,
    DomainSearchUserUsageBucketsInput,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    AdminSearchDomainUsageBucketsPayload,
    AdminSearchProjectUsageBucketsPayload,
    AdminSearchUserUsageBucketsPayload,
    DomainSearchDomainUsageBucketsPayload,
    DomainSearchProjectUsageBucketsPayload,
    DomainSearchUserUsageBucketsPayload,
    DomainUsageBucketNode,
    ProjectUsageBucketNode,
    UserUsageBucketNode,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.resource_usage_history import (
    DomainUsageBucketConditions,
    DomainUsageBucketData,
    DomainUsageBucketOrders,
    DomainUsageBucketSearchScope,
    ProjectUsageBucketConditions,
    ProjectUsageBucketData,
    ProjectUsageBucketOrders,
    ProjectUsageBucketSearchScope,
    UserUsageBucketConditions,
    UserUsageBucketData,
    UserUsageBucketOrders,
    UserUsageBucketSearchScope,
)
from ai.backend.manager.services.resource_usage.actions import (
    SearchDomainUsageBucketsAction,
    SearchProjectUsageBucketsAction,
    SearchScopedDomainUsageBucketsAction,
    SearchScopedProjectUsageBucketsAction,
    SearchScopedUserUsageBucketsAction,
    SearchUserUsageBucketsAction,
)

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 20


class ResourceUsageAdapter(BaseAdapter):
    """Adapter for resource usage domain operations."""

    # Admin (unscoped) searches

    async def admin_search_domain(
        self, input: AdminSearchDomainUsageBucketsInput
    ) -> AdminSearchDomainUsageBucketsPayload:
        """Search domain usage buckets without scope restriction."""
        limit = input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT
        offset = input.offset if input.offset is not None else 0
        pagination = OffsetPagination(limit=limit, offset=offset)
        conditions = []
        if input.domain_name is not None:
            conditions.append(DomainUsageBucketConditions.by_domain_name(input.domain_name))
        if input.resource_group is not None:
            conditions.append(DomainUsageBucketConditions.by_resource_group(input.resource_group))
        orders = [DomainUsageBucketOrders.by_period_start(ascending=False)]
        action_result = (
            await self._processors.resource_usage.search_domain_usage_buckets.wait_for_complete(
                SearchDomainUsageBucketsAction(
                    pagination=pagination,
                    conditions=conditions,
                    orders=orders,
                )
            )
        )
        has_next_page = (offset + len(action_result.items)) < action_result.total_count
        has_previous_page = offset > 0
        return AdminSearchDomainUsageBucketsPayload(
            items=[self._domain_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    async def admin_search_project(
        self, input: AdminSearchProjectUsageBucketsInput
    ) -> AdminSearchProjectUsageBucketsPayload:
        """Search project usage buckets without scope restriction."""
        limit = input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT
        offset = input.offset if input.offset is not None else 0
        pagination = OffsetPagination(limit=limit, offset=offset)
        conditions = []
        if input.domain_name is not None:
            conditions.append(ProjectUsageBucketConditions.by_domain_name(input.domain_name))
        if input.resource_group is not None:
            conditions.append(ProjectUsageBucketConditions.by_resource_group(input.resource_group))
        if input.project_id is not None:
            conditions.append(
                ProjectUsageBucketConditions.by_project_id(
                    UUIDEqualMatchSpec(value=input.project_id, negated=False)
                )
            )
        orders = [ProjectUsageBucketOrders.by_period_start(ascending=False)]
        action_result = (
            await self._processors.resource_usage.search_project_usage_buckets.wait_for_complete(
                SearchProjectUsageBucketsAction(
                    pagination=pagination,
                    conditions=conditions,
                    orders=orders,
                )
            )
        )
        has_next_page = (offset + len(action_result.items)) < action_result.total_count
        has_previous_page = offset > 0
        return AdminSearchProjectUsageBucketsPayload(
            items=[self._project_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    async def admin_search_user(
        self, input: AdminSearchUserUsageBucketsInput
    ) -> AdminSearchUserUsageBucketsPayload:
        """Search user usage buckets without scope restriction."""
        limit = input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT
        offset = input.offset if input.offset is not None else 0
        pagination = OffsetPagination(limit=limit, offset=offset)
        conditions = []
        if input.domain_name is not None:
            conditions.append(UserUsageBucketConditions.by_domain_name(input.domain_name))
        if input.resource_group is not None:
            conditions.append(UserUsageBucketConditions.by_resource_group(input.resource_group))
        if input.project_id is not None:
            conditions.append(
                UserUsageBucketConditions.by_project_id(
                    UUIDEqualMatchSpec(value=input.project_id, negated=False)
                )
            )
        if input.user_uuid is not None:
            conditions.append(
                UserUsageBucketConditions.by_user_uuid(
                    UUIDEqualMatchSpec(value=input.user_uuid, negated=False)
                )
            )
        orders = [UserUsageBucketOrders.by_period_start(ascending=False)]
        action_result = (
            await self._processors.resource_usage.search_user_usage_buckets.wait_for_complete(
                SearchUserUsageBucketsAction(
                    pagination=pagination,
                    conditions=conditions,
                    orders=orders,
                )
            )
        )
        has_next_page = (offset + len(action_result.items)) < action_result.total_count
        has_previous_page = offset > 0
        return AdminSearchUserUsageBucketsPayload(
            items=[self._user_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    # Scoped searches

    async def domain_search_domain(
        self, input: DomainSearchDomainUsageBucketsInput
    ) -> DomainSearchDomainUsageBucketsPayload:
        """Search domain usage buckets scoped to a domain/resource-group."""
        limit = input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT
        offset = input.offset if input.offset is not None else 0
        scope = DomainUsageBucketSearchScope(
            domain_name=input.domain_name,
            resource_group=input.resource_group,
        )
        querier = BatchQuerier(
            conditions=[],
            orders=[DomainUsageBucketOrders.by_period_start(ascending=False)],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action_result = await self._processors.resource_usage.search_scoped_domain_usage_buckets.wait_for_complete(
            SearchScopedDomainUsageBucketsAction(scope=scope, querier=querier)
        )
        has_next_page = (offset + len(action_result.items)) < action_result.total_count
        has_previous_page = offset > 0
        return DomainSearchDomainUsageBucketsPayload(
            items=[self._domain_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    async def domain_search_project(
        self, input: DomainSearchProjectUsageBucketsInput
    ) -> DomainSearchProjectUsageBucketsPayload:
        """Search project usage buckets scoped to a domain/resource-group/project."""
        limit = input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT
        offset = input.offset if input.offset is not None else 0
        scope = ProjectUsageBucketSearchScope(
            domain_name=input.domain_name,
            resource_group=input.resource_group,
            project_id=input.project_id,
        )
        querier = BatchQuerier(
            conditions=[],
            orders=[ProjectUsageBucketOrders.by_period_start(ascending=False)],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action_result = await self._processors.resource_usage.search_scoped_project_usage_buckets.wait_for_complete(
            SearchScopedProjectUsageBucketsAction(scope=scope, querier=querier)
        )
        has_next_page = (offset + len(action_result.items)) < action_result.total_count
        has_previous_page = offset > 0
        return DomainSearchProjectUsageBucketsPayload(
            items=[self._project_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    async def domain_search_user(
        self, input: DomainSearchUserUsageBucketsInput
    ) -> DomainSearchUserUsageBucketsPayload:
        """Search user usage buckets scoped to a domain/resource-group/project/user."""
        limit = input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT
        offset = input.offset if input.offset is not None else 0
        scope = UserUsageBucketSearchScope(
            domain_name=input.domain_name,
            resource_group=input.resource_group,
            project_id=input.project_id,
            user_uuid=input.user_uuid,
        )
        querier = BatchQuerier(
            conditions=[],
            orders=[UserUsageBucketOrders.by_period_start(ascending=False)],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action_result = await self._processors.resource_usage.search_scoped_user_usage_buckets.wait_for_complete(
            SearchScopedUserUsageBucketsAction(scope=scope, querier=querier)
        )
        has_next_page = (offset + len(action_result.items)) < action_result.total_count
        has_previous_page = offset > 0
        return DomainSearchUserUsageBucketsPayload(
            items=[self._user_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    @staticmethod
    def _domain_bucket_to_dto(data: DomainUsageBucketData) -> DomainUsageBucketNode:
        return DomainUsageBucketNode(
            id=data.id,
            domain_name=data.domain_name,
            resource_group=data.resource_group,
            period_start=data.period_start,
            period_end=data.period_end,
            decay_unit_days=data.decay_unit_days,
            resource_usage=dict(data.resource_usage),
            capacity_snapshot=dict(data.capacity_snapshot),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _project_bucket_to_dto(data: ProjectUsageBucketData) -> ProjectUsageBucketNode:
        return ProjectUsageBucketNode(
            id=data.id,
            project_id=data.project_id,
            domain_name=data.domain_name,
            resource_group=data.resource_group,
            period_start=data.period_start,
            period_end=data.period_end,
            decay_unit_days=data.decay_unit_days,
            resource_usage=dict(data.resource_usage),
            capacity_snapshot=dict(data.capacity_snapshot),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _user_bucket_to_dto(data: UserUsageBucketData) -> UserUsageBucketNode:
        return UserUsageBucketNode(
            id=data.id,
            user_uuid=data.user_uuid,
            project_id=data.project_id,
            domain_name=data.domain_name,
            resource_group=data.resource_group,
            period_start=data.period_start,
            period_end=data.period_end,
            decay_unit_days=data.decay_unit_days,
            resource_usage=dict(data.resource_usage),
            capacity_snapshot=dict(data.capacity_snapshot),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
