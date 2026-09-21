"""Resource Usage adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

from ai.backend.common.data.entity.resource_group import (
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDEqualMatchSpec
from ai.backend.common.dto.manager.v2.fair_share.types import (
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
)
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    AdminSearchDomainUsageBucketsInput,
    AdminSearchProjectUsageBucketsInput,
    AdminSearchUserUsageBucketsInput,
    DomainSearchDomainUsageBucketsInput,
    DomainSearchProjectUsageBucketsInput,
    DomainSearchUserUsageBucketsInput,
    DomainUsageBucketFilter,
    DomainUsageBucketOrderBy,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrderBy,
    UserUsageBucketFilter,
    UserUsageBucketOrderBy,
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
    UsageBucketMetadataNode,
    UserUsageBucketNode,
)
from ai.backend.common.dto.manager.v2.resource_usage.types import (
    OrderDirection,
    UsageBucketOrderField,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.resource_usage_history.scopes import (
    DomainUsageBucketTarget,
    ProjectUsageBucketTarget,
    UserUsageBucketTarget,
)
from ai.backend.manager.models.resource_usage_history.searchable_fields import (
    DomainUsageBucketSearchableFields,
    ProjectUsageBucketSearchableFields,
    UserUsageBucketSearchableFields,
)
from ai.backend.manager.models.resource_usage_history.searchers import (
    DomainUsageBucketSearcher,
    ProjectUsageBucketSearcher,
    UserUsageBucketSearcher,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.resource_usage_history import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.services.resource_group.actions.lookup import LookupResourceGroupAction
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_usage.actions.global_search_domain_usage_buckets import (
    GlobalSearchDomainUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.global_search_project_usage_buckets import (
    GlobalSearchProjectUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.global_search_user_usage_buckets import (
    GlobalSearchUserUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.search_domain_usage_buckets import (
    SearchDomainUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.search_project_usage_buckets import (
    SearchProjectUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.actions.search_user_usage_buckets import (
    SearchUserUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors

DEFAULT_PAGINATION_LIMIT = 20

_DOMAIN_USAGE_BUCKET_PAGINATION_SPEC = PaginationSpec(
    forward_order=DomainUsageBucketSearchableFields.own.period_start.order.apply(ascending=False),
    cursor_column=DomainUsageBucketRow.id,
)

_PROJECT_USAGE_BUCKET_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectUsageBucketSearchableFields.own.period_start.order.apply(ascending=False),
    cursor_column=ProjectUsageBucketRow.id,
)

_USER_USAGE_BUCKET_PAGINATION_SPEC = PaginationSpec(
    forward_order=UserUsageBucketSearchableFields.own.period_start.order.apply(ascending=False),
    cursor_column=UserUsageBucketRow.id,
)


class ResourceUsageAdapter(BaseAdapter):
    """Adapter for resource usage domain operations."""

    _resource_usage: ResourceUsageProcessors
    _resource_group: ResourceGroupProcessors

    def __init__(
        self,
        resource_usage: ResourceUsageProcessors,
        resource_group: ResourceGroupProcessors,
    ) -> None:
        self._resource_usage = resource_usage
        self._resource_group = resource_group

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
            conditions.append(
                DomainUsageBucketSearchableFields.own.domain_name.filter.equals(
                    StringMatchSpec(input.domain_name, case_insensitive=False, negated=False)
                )
            )
        if input.resource_group is not None:
            conditions.append(
                DomainUsageBucketSearchableFields.own.resource_group.filter.equals(
                    StringMatchSpec(input.resource_group, case_insensitive=False, negated=False)
                )
            )
        orders = [DomainUsageBucketSearchableFields.own.period_start.order.apply(ascending=False)]
        action_result = await self._resource_usage.global_search_domain_usage_buckets.run(
            GlobalSearchDomainUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=DomainUsageBucketSearcher(
                        pagination=pagination,
                        conditions=conditions,
                        orders=orders,
                    ),
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
            conditions.append(
                ProjectUsageBucketSearchableFields.own.domain_name.filter.equals(
                    StringMatchSpec(input.domain_name, case_insensitive=False, negated=False)
                )
            )
        if input.resource_group is not None:
            conditions.append(
                ProjectUsageBucketSearchableFields.own.resource_group.filter.equals(
                    StringMatchSpec(input.resource_group, case_insensitive=False, negated=False)
                )
            )
        if input.project_id is not None:
            conditions.append(
                ProjectUsageBucketSearchableFields.own.project_id.filter.equals(
                    UUIDEqualMatchSpec(value=input.project_id, negated=False)
                )
            )
        orders = [ProjectUsageBucketSearchableFields.own.period_start.order.apply(ascending=False)]
        action_result = await self._resource_usage.global_search_project_usage_buckets.run(
            GlobalSearchProjectUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=ProjectUsageBucketSearcher(
                        pagination=pagination,
                        conditions=conditions,
                        orders=orders,
                    ),
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
            conditions.append(
                UserUsageBucketSearchableFields.own.domain_name.filter.equals(
                    StringMatchSpec(input.domain_name, case_insensitive=False, negated=False)
                )
            )
        if input.resource_group is not None:
            conditions.append(
                UserUsageBucketSearchableFields.own.resource_group.filter.equals(
                    StringMatchSpec(input.resource_group, case_insensitive=False, negated=False)
                )
            )
        if input.project_id is not None:
            conditions.append(
                UserUsageBucketSearchableFields.own.project_id.filter.equals(
                    UUIDEqualMatchSpec(value=input.project_id, negated=False)
                )
            )
        if input.user_uuid is not None:
            conditions.append(
                UserUsageBucketSearchableFields.own.user_uuid.filter.equals(
                    UUIDEqualMatchSpec(value=input.user_uuid, negated=False)
                )
            )
        orders = [UserUsageBucketSearchableFields.own.period_start.order.apply(ascending=False)]
        action_result = await self._resource_usage.global_search_user_usage_buckets.run(
            GlobalSearchUserUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=UserUsageBucketSearcher(
                        pagination=pagination,
                        conditions=conditions,
                        orders=orders,
                    ),
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
        resource_group_id = await self._resource_group_id(input.resource_group)
        querier = BatchQuerier(
            conditions=[],
            orders=[
                DomainUsageBucketSearchableFields.own.period_start.order.apply(ascending=False)
            ],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action_result = await self._resource_usage.search_domain_usage_buckets.run(
            SearchDomainUsageBucketsAction(
                targets=[
                    DomainUsageBucketTarget(
                        resource_group_id=resource_group_id,
                        domain_name=input.domain_name,
                    )
                ],
                searcher=DomainUsageBucketSearcher(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                ),
            )
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
        resource_group_id = await self._resource_group_id(input.resource_group)
        querier = BatchQuerier(
            conditions=[],
            orders=[
                ProjectUsageBucketSearchableFields.own.period_start.order.apply(ascending=False)
            ],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action_result = await self._resource_usage.search_project_usage_buckets.run(
            SearchProjectUsageBucketsAction(
                targets=[
                    ProjectUsageBucketTarget(
                        resource_group_id=resource_group_id,
                        domain_name=input.domain_name,
                        project_id=input.project_id,
                    )
                ],
                searcher=ProjectUsageBucketSearcher(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                ),
            )
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
        resource_group_id = await self._resource_group_id(input.resource_group)
        querier = BatchQuerier(
            conditions=[],
            orders=[UserUsageBucketSearchableFields.own.period_start.order.apply(ascending=False)],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action_result = await self._resource_usage.search_user_usage_buckets.run(
            SearchUserUsageBucketsAction(
                targets=[
                    UserUsageBucketTarget(
                        resource_group_id=resource_group_id,
                        domain_name=input.domain_name,
                        project_id=input.project_id,
                        user_uuid=input.user_uuid,
                    )
                ],
                searcher=UserUsageBucketSearcher(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                ),
            )
        )
        has_next_page = (offset + len(action_result.items)) < action_result.total_count
        has_previous_page = offset > 0
        return DomainSearchUserUsageBucketsPayload(
            items=[self._user_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    # GQL search methods (cursor/offset pagination with pydantic filter DTOs)

    async def gql_search_domain_scoped(
        self,
        resource_group_name: str,
        domain_name: str,
        filter: DomainUsageBucketFilter | None = None,
        order: list[DomainUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchDomainUsageBucketsPayload:
        """Search domain usage buckets scoped to a domain/resource-group (GQL pagination)."""
        conditions = self._convert_domain_filter(filter) if filter else []
        orders = self._convert_domain_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_DOMAIN_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        resource_group_id = await self._resource_group_id(resource_group_name)
        action_result = await self._resource_usage.search_domain_usage_buckets.run(
            SearchDomainUsageBucketsAction(
                targets=[
                    DomainUsageBucketTarget(
                        resource_group_id=resource_group_id,
                        domain_name=domain_name,
                    )
                ],
                searcher=DomainUsageBucketSearcher(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                ),
            )
        )
        return AdminSearchDomainUsageBucketsPayload(
            items=[self._domain_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_project_scoped(
        self,
        resource_group_name: str,
        domain_name: str,
        project_id: uuid.UUID,
        filter: ProjectUsageBucketFilter | None = None,
        order: list[ProjectUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchProjectUsageBucketsPayload:
        """Search project usage buckets scoped to project/domain/resource-group (GQL pagination)."""
        conditions = self._convert_project_filter(filter) if filter else []
        orders = self._convert_project_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        resource_group_id = await self._resource_group_id(resource_group_name)
        action_result = await self._resource_usage.search_project_usage_buckets.run(
            SearchProjectUsageBucketsAction(
                targets=[
                    ProjectUsageBucketTarget(
                        resource_group_id=resource_group_id,
                        domain_name=domain_name,
                        project_id=project_id,
                    )
                ],
                searcher=ProjectUsageBucketSearcher(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                ),
            )
        )
        return AdminSearchProjectUsageBucketsPayload(
            items=[self._project_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_user_scoped(
        self,
        resource_group_name: str,
        domain_name: str,
        project_id: uuid.UUID,
        user_uuid: uuid.UUID,
        filter: UserUsageBucketFilter | None = None,
        order: list[UserUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchUserUsageBucketsPayload:
        """Search user usage buckets scoped to user/project/domain/resource-group (GQL pagination)."""
        conditions = self._convert_user_filter(filter) if filter else []
        orders = self._convert_user_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_USER_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        resource_group_id = await self._resource_group_id(resource_group_name)
        action_result = await self._resource_usage.search_user_usage_buckets.run(
            SearchUserUsageBucketsAction(
                targets=[
                    UserUsageBucketTarget(
                        resource_group_id=resource_group_id,
                        domain_name=domain_name,
                        project_id=project_id,
                        user_uuid=user_uuid,
                    )
                ],
                searcher=UserUsageBucketSearcher(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                ),
            )
        )
        return AdminSearchUserUsageBucketsPayload(
            items=[self._user_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_admin_search_domain(
        self,
        filter: DomainUsageBucketFilter | None = None,
        order: list[DomainUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchDomainUsageBucketsPayload:
        """Search domain usage buckets without scope restriction (GQL pagination)."""
        conditions = self._convert_domain_filter(filter) if filter else []
        orders = self._convert_domain_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_DOMAIN_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        action_result = await self._resource_usage.global_search_domain_usage_buckets.run(
            GlobalSearchDomainUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=DomainUsageBucketSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return AdminSearchDomainUsageBucketsPayload(
            items=[self._domain_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_admin_search_project(
        self,
        filter: ProjectUsageBucketFilter | None = None,
        order: list[ProjectUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchProjectUsageBucketsPayload:
        """Search project usage buckets without scope restriction (GQL pagination)."""
        conditions = self._convert_project_filter(filter) if filter else []
        orders = self._convert_project_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        action_result = await self._resource_usage.global_search_project_usage_buckets.run(
            GlobalSearchProjectUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=ProjectUsageBucketSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return AdminSearchProjectUsageBucketsPayload(
            items=[self._project_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_admin_search_user(
        self,
        filter: UserUsageBucketFilter | None = None,
        order: list[UserUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchUserUsageBucketsPayload:
        """Search user usage buckets without scope restriction (GQL pagination)."""
        conditions = self._convert_user_filter(filter) if filter else []
        orders = self._convert_user_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_USER_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        action_result = await self._resource_usage.global_search_user_usage_buckets.run(
            GlobalSearchUserUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=UserUsageBucketSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return AdminSearchUserUsageBucketsPayload(
            items=[self._user_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_project_unscoped(
        self,
        base_conditions: list[QueryCondition],
        filter: ProjectUsageBucketFilter | None = None,
        order: list[ProjectUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchProjectUsageBucketsPayload:
        """Search project usage buckets with base conditions (for nested resolvers)."""
        conditions = self._convert_project_filter(filter) if filter else []
        orders = self._convert_project_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_PROJECT_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
            base_conditions=base_conditions,
        )
        action_result = await self._resource_usage.global_search_project_usage_buckets.run(
            GlobalSearchProjectUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=ProjectUsageBucketSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return AdminSearchProjectUsageBucketsPayload(
            items=[self._project_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_user_unscoped(
        self,
        base_conditions: list[QueryCondition],
        filter: UserUsageBucketFilter | None = None,
        order: list[UserUsageBucketOrderBy] | None = None,
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AdminSearchUserUsageBucketsPayload:
        """Search user usage buckets with base conditions (for nested resolvers)."""
        conditions = self._convert_user_filter(filter) if filter else []
        orders = self._convert_user_orders(order) if order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_USER_USAGE_BUCKET_PAGINATION_SPEC,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
            base_conditions=base_conditions,
        )
        action_result = await self._resource_usage.global_search_user_usage_buckets.run(
            GlobalSearchUserUsageBucketsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=UserUsageBucketSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return AdminSearchUserUsageBucketsPayload(
            items=[self._user_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    # Filter/order conversion helpers

    def _convert_domain_filter(
        self,
        filter_req: DomainUsageBucketFilter,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.resource_group is not None:
            conditions.extend(
                self.apply_string_filter(
                    filter_req.resource_group,
                    DomainUsageBucketSearchableFields.own.resource_group.filter,
                )
            )

        if filter_req.domain_name is not None:
            conditions.extend(
                self.apply_string_filter(
                    filter_req.domain_name, DomainUsageBucketSearchableFields.own.domain_name.filter
                )
            )

        if filter_req.period_start is not None:
            conditions.extend(
                self.apply_date_filter(
                    filter_req.period_start,
                    DomainUsageBucketSearchableFields.own.period_start.filter,
                )
            )

        if filter_req.period_end is not None:
            conditions.extend(
                self.apply_date_filter(
                    filter_req.period_end, DomainUsageBucketSearchableFields.own.period_end.filter
                )
            )

        if filter_req.AND:
            for sub_filter in filter_req.AND:
                conditions.extend(self._convert_domain_filter(sub_filter))

        if filter_req.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.OR:
                or_conditions.extend(self._convert_domain_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))

        if filter_req.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter_req.NOT:
                not_conditions.extend(self._convert_domain_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

        return conditions

    @staticmethod
    def _convert_domain_orders(
        orders: list[DomainUsageBucketOrderBy],
    ) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            if order.field == UsageBucketOrderField.PERIOD_START:
                result.append(
                    DomainUsageBucketSearchableFields.own.period_start.order.apply(ascending)
                )
        return result

    def _convert_project_filter(
        self,
        filter_req: ProjectUsageBucketFilter,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.resource_group is not None:
            conditions.extend(
                self.apply_string_filter(
                    filter_req.resource_group,
                    ProjectUsageBucketSearchableFields.own.resource_group.filter,
                )
            )

        if filter_req.project_id is not None:
            conditions.extend(
                self.apply_uuid_filter(
                    filter_req.project_id, ProjectUsageBucketSearchableFields.own.project_id.filter
                )
            )

        if filter_req.domain_name is not None:
            conditions.extend(
                self.apply_string_filter(
                    filter_req.domain_name,
                    ProjectUsageBucketSearchableFields.own.domain_name.filter,
                )
            )

        if filter_req.period_start is not None:
            conditions.extend(
                self.apply_date_filter(
                    filter_req.period_start,
                    ProjectUsageBucketSearchableFields.own.period_start.filter,
                )
            )

        if filter_req.period_end is not None:
            conditions.extend(
                self.apply_date_filter(
                    filter_req.period_end, ProjectUsageBucketSearchableFields.own.period_end.filter
                )
            )

        if filter_req.AND:
            for sub_filter in filter_req.AND:
                conditions.extend(self._convert_project_filter(sub_filter))

        if filter_req.OR:
            or_conditions_p: list[QueryCondition] = []
            for sub_filter in filter_req.OR:
                or_conditions_p.extend(self._convert_project_filter(sub_filter))
            if or_conditions_p:
                conditions.append(combine_conditions_or(or_conditions_p))

        if filter_req.NOT:
            not_conditions_p: list[QueryCondition] = []
            for sub_filter in filter_req.NOT:
                not_conditions_p.extend(self._convert_project_filter(sub_filter))
            if not_conditions_p:
                conditions.append(negate_conditions(not_conditions_p))

        return conditions

    @staticmethod
    def _convert_project_orders(
        orders: list[ProjectUsageBucketOrderBy],
    ) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            if order.field == UsageBucketOrderField.PERIOD_START:
                result.append(
                    ProjectUsageBucketSearchableFields.own.period_start.order.apply(ascending)
                )
        return result

    def _convert_user_filter(
        self,
        filter_req: UserUsageBucketFilter,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.resource_group is not None:
            conditions.extend(
                self.apply_string_filter(
                    filter_req.resource_group,
                    UserUsageBucketSearchableFields.own.resource_group.filter,
                )
            )

        if filter_req.user_uuid is not None:
            conditions.extend(
                self.apply_uuid_filter(
                    filter_req.user_uuid, UserUsageBucketSearchableFields.own.user_uuid.filter
                )
            )

        if filter_req.project_id is not None:
            conditions.extend(
                self.apply_uuid_filter(
                    filter_req.project_id, UserUsageBucketSearchableFields.own.project_id.filter
                )
            )

        if filter_req.domain_name is not None:
            conditions.extend(
                self.apply_string_filter(
                    filter_req.domain_name, UserUsageBucketSearchableFields.own.domain_name.filter
                )
            )

        if filter_req.period_start is not None:
            conditions.extend(
                self.apply_date_filter(
                    filter_req.period_start, UserUsageBucketSearchableFields.own.period_start.filter
                )
            )

        if filter_req.period_end is not None:
            conditions.extend(
                self.apply_date_filter(
                    filter_req.period_end, UserUsageBucketSearchableFields.own.period_end.filter
                )
            )

        if filter_req.AND:
            for sub_filter in filter_req.AND:
                conditions.extend(self._convert_user_filter(sub_filter))

        if filter_req.OR:
            or_conditions_u: list[QueryCondition] = []
            for sub_filter in filter_req.OR:
                or_conditions_u.extend(self._convert_user_filter(sub_filter))
            if or_conditions_u:
                conditions.append(combine_conditions_or(or_conditions_u))

        if filter_req.NOT:
            not_conditions_u: list[QueryCondition] = []
            for sub_filter in filter_req.NOT:
                not_conditions_u.extend(self._convert_user_filter(sub_filter))
            if not_conditions_u:
                conditions.append(negate_conditions(not_conditions_u))

        return conditions

    @staticmethod
    def _convert_user_orders(
        orders: list[UserUsageBucketOrderBy],
    ) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            if order.field == UsageBucketOrderField.PERIOD_START:
                result.append(
                    UserUsageBucketSearchableFields.own.period_start.order.apply(ascending)
                )
        return result

    @staticmethod
    def _resource_slot_to_info(slot: Mapping[str, Decimal]) -> ResourceSlotInfo:
        return ResourceSlotInfo(
            entries=[ResourceSlotEntryInfo(resource_type=k, quantity=v) for k, v in slot.items()]
        )

    @staticmethod
    def _domain_bucket_to_dto(data: DomainUsageBucketData) -> DomainUsageBucketNode:
        return DomainUsageBucketNode(
            id=data.id,
            field_id=data.id,
            domain_name=data.domain_name,
            resource_group_name=data.resource_group,
            metadata=UsageBucketMetadataNode(
                period_start=data.period_start,
                period_end=data.period_end,
                decay_unit_days=data.decay_unit_days,
                created_at=data.created_at,
                updated_at=data.updated_at,
            ),
            resource_usage=ResourceUsageAdapter._resource_slot_to_info(data.resource_usage),
            capacity_snapshot=ResourceUsageAdapter._resource_slot_to_info(data.capacity_snapshot),
        )

    @staticmethod
    def _project_bucket_to_dto(data: ProjectUsageBucketData) -> ProjectUsageBucketNode:
        return ProjectUsageBucketNode(
            id=data.id,
            field_id=data.id,
            project_id=data.project_id,
            domain_name=data.domain_name,
            resource_group_name=data.resource_group,
            metadata=UsageBucketMetadataNode(
                period_start=data.period_start,
                period_end=data.period_end,
                decay_unit_days=data.decay_unit_days,
                created_at=data.created_at,
                updated_at=data.updated_at,
            ),
            resource_usage=ResourceUsageAdapter._resource_slot_to_info(data.resource_usage),
            capacity_snapshot=ResourceUsageAdapter._resource_slot_to_info(data.capacity_snapshot),
        )

    @staticmethod
    def _user_bucket_to_dto(data: UserUsageBucketData) -> UserUsageBucketNode:
        return UserUsageBucketNode(
            id=data.id,
            field_id=data.id,
            user_uuid=data.user_uuid,
            project_id=data.project_id,
            domain_name=data.domain_name,
            resource_group_name=data.resource_group,
            metadata=UsageBucketMetadataNode(
                period_start=data.period_start,
                period_end=data.period_end,
                decay_unit_days=data.decay_unit_days,
                created_at=data.created_at,
                updated_at=data.updated_at,
            ),
            resource_usage=ResourceUsageAdapter._resource_slot_to_info(data.resource_usage),
            capacity_snapshot=ResourceUsageAdapter._resource_slot_to_info(data.capacity_snapshot),
        )

    async def _resource_group_id(self, name: str) -> ResourceGroupID:
        """The resource group's id, which is what a bucket read is answered for.

        The request names the group; a scope has to name its id.
        """
        result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(name))
        )
        return result.entity_id()
