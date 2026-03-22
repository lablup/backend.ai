"""Resource Usage adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date
from decimal import Decimal

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.dto.manager.query import DateFilter as DateFilterDTO
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
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
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
from .pagination import PaginationSpec

DEFAULT_PAGINATION_LIMIT = 20

_DOMAIN_USAGE_BUCKET_PAGINATION_SPEC = PaginationSpec(
    forward_order=DomainUsageBucketOrders.by_period_start(ascending=False),
    backward_order=DomainUsageBucketOrders.by_period_start(ascending=True),
    forward_condition_factory=DomainUsageBucketConditions.by_cursor_forward,
    backward_condition_factory=DomainUsageBucketConditions.by_cursor_backward,
    tiebreaker_order=DomainUsageBucketRow.id.asc(),
)

_PROJECT_USAGE_BUCKET_PAGINATION_SPEC = PaginationSpec(
    forward_order=ProjectUsageBucketOrders.by_period_start(ascending=False),
    backward_order=ProjectUsageBucketOrders.by_period_start(ascending=True),
    forward_condition_factory=ProjectUsageBucketConditions.by_cursor_forward,
    backward_condition_factory=ProjectUsageBucketConditions.by_cursor_backward,
    tiebreaker_order=ProjectUsageBucketRow.id.asc(),
)

_USER_USAGE_BUCKET_PAGINATION_SPEC = PaginationSpec(
    forward_order=UserUsageBucketOrders.by_period_start(ascending=False),
    backward_order=UserUsageBucketOrders.by_period_start(ascending=True),
    forward_condition_factory=UserUsageBucketConditions.by_cursor_forward,
    backward_condition_factory=UserUsageBucketConditions.by_cursor_backward,
    tiebreaker_order=UserUsageBucketRow.id.asc(),
)


def _build_date_filter_condition(
    date_filter: DateFilterDTO,
    before_factory: Callable[[date], QueryCondition],
    after_factory: Callable[[date], QueryCondition],
    equals_factory: Callable[[date], QueryCondition],
    not_equals_factory: Callable[[date], QueryCondition],
) -> QueryCondition | None:
    """Convert a DateFilterDTO into a single QueryCondition."""
    if date_filter.not_equals is not None:
        return not_equals_factory(date_filter.not_equals)
    if date_filter.equals is not None:
        return equals_factory(date_filter.equals)
    if date_filter.before is not None:
        return before_factory(date_filter.before)
    if date_filter.after is not None:
        return after_factory(date_filter.after)
    return None


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

    # GQL search methods (cursor/offset pagination with pydantic filter DTOs)

    async def gql_search_domain_scoped(
        self,
        scope: DomainUsageBucketSearchScope,
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
        action_result = await self._processors.resource_usage.search_scoped_domain_usage_buckets.wait_for_complete(
            SearchScopedDomainUsageBucketsAction(scope=scope, querier=querier)
        )
        return AdminSearchDomainUsageBucketsPayload(
            items=[self._domain_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_project_scoped(
        self,
        scope: ProjectUsageBucketSearchScope,
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
        action_result = await self._processors.resource_usage.search_scoped_project_usage_buckets.wait_for_complete(
            SearchScopedProjectUsageBucketsAction(scope=scope, querier=querier)
        )
        return AdminSearchProjectUsageBucketsPayload(
            items=[self._project_bucket_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def gql_search_user_scoped(
        self,
        scope: UserUsageBucketSearchScope,
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
        action_result = await self._processors.resource_usage.search_scoped_user_usage_buckets.wait_for_complete(
            SearchScopedUserUsageBucketsAction(scope=scope, querier=querier)
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
        action_result = (
            await self._processors.resource_usage.search_domain_usage_buckets.wait_for_complete(
                SearchDomainUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
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
        action_result = (
            await self._processors.resource_usage.search_project_usage_buckets.wait_for_complete(
                SearchProjectUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
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
        action_result = (
            await self._processors.resource_usage.search_user_usage_buckets.wait_for_complete(
                SearchUserUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
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
        action_result = (
            await self._processors.resource_usage.search_project_usage_buckets.wait_for_complete(
                SearchProjectUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
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
        action_result = (
            await self._processors.resource_usage.search_user_usage_buckets.wait_for_complete(
                SearchUserUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
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
            condition = self.convert_string_filter(
                filter_req.resource_group,
                contains_factory=DomainUsageBucketConditions.by_resource_group_contains,
                equals_factory=DomainUsageBucketConditions.by_resource_group_equals,
                starts_with_factory=DomainUsageBucketConditions.by_resource_group_starts_with,
                ends_with_factory=DomainUsageBucketConditions.by_resource_group_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.domain_name is not None:
            condition = self.convert_string_filter(
                filter_req.domain_name,
                contains_factory=DomainUsageBucketConditions.by_domain_name_contains,
                equals_factory=DomainUsageBucketConditions.by_domain_name_equals,
                starts_with_factory=DomainUsageBucketConditions.by_domain_name_starts_with,
                ends_with_factory=DomainUsageBucketConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.period_start is not None:
            ps_condition = _build_date_filter_condition(
                filter_req.period_start,
                before_factory=DomainUsageBucketConditions.by_period_start_before,
                after_factory=DomainUsageBucketConditions.by_period_start_after,
                equals_factory=DomainUsageBucketConditions.by_period_start,
                not_equals_factory=DomainUsageBucketConditions.by_period_start_not_equals,
            )
            if ps_condition is not None:
                conditions.append(ps_condition)

        if filter_req.period_end is not None:
            pe_condition = _build_date_filter_condition(
                filter_req.period_end,
                before_factory=DomainUsageBucketConditions.by_period_end_before,
                after_factory=DomainUsageBucketConditions.by_period_end_after,
                equals_factory=DomainUsageBucketConditions.by_period_end,
                not_equals_factory=DomainUsageBucketConditions.by_period_end_not_equals,
            )
            if pe_condition is not None:
                conditions.append(pe_condition)

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
                result.append(DomainUsageBucketOrders.by_period_start(ascending))
        return result

    def _convert_project_filter(
        self,
        filter_req: ProjectUsageBucketFilter,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.resource_group is not None:
            condition = self.convert_string_filter(
                filter_req.resource_group,
                contains_factory=ProjectUsageBucketConditions.by_resource_group_contains,
                equals_factory=ProjectUsageBucketConditions.by_resource_group_equals,
                starts_with_factory=ProjectUsageBucketConditions.by_resource_group_starts_with,
                ends_with_factory=ProjectUsageBucketConditions.by_resource_group_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.project_id is not None:
            condition = self.convert_uuid_filter(
                filter_req.project_id,
                equals_factory=ProjectUsageBucketConditions.by_project_id,
                in_factory=ProjectUsageBucketConditions.by_project_ids,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.domain_name is not None:
            condition = self.convert_string_filter(
                filter_req.domain_name,
                contains_factory=ProjectUsageBucketConditions.by_domain_name_contains,
                equals_factory=ProjectUsageBucketConditions.by_domain_name_equals,
                starts_with_factory=ProjectUsageBucketConditions.by_domain_name_starts_with,
                ends_with_factory=ProjectUsageBucketConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.period_start is not None:
            ps_condition = _build_date_filter_condition(
                filter_req.period_start,
                before_factory=ProjectUsageBucketConditions.by_period_start_before,
                after_factory=ProjectUsageBucketConditions.by_period_start_after,
                equals_factory=ProjectUsageBucketConditions.by_period_start,
                not_equals_factory=ProjectUsageBucketConditions.by_period_start_not_equals,
            )
            if ps_condition is not None:
                conditions.append(ps_condition)

        if filter_req.period_end is not None:
            pe_condition = _build_date_filter_condition(
                filter_req.period_end,
                before_factory=ProjectUsageBucketConditions.by_period_end_before,
                after_factory=ProjectUsageBucketConditions.by_period_end_after,
                equals_factory=ProjectUsageBucketConditions.by_period_end,
                not_equals_factory=ProjectUsageBucketConditions.by_period_end_not_equals,
            )
            if pe_condition is not None:
                conditions.append(pe_condition)

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
                result.append(ProjectUsageBucketOrders.by_period_start(ascending))
        return result

    def _convert_user_filter(
        self,
        filter_req: UserUsageBucketFilter,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter_req.resource_group is not None:
            condition = self.convert_string_filter(
                filter_req.resource_group,
                contains_factory=UserUsageBucketConditions.by_resource_group_contains,
                equals_factory=UserUsageBucketConditions.by_resource_group_equals,
                starts_with_factory=UserUsageBucketConditions.by_resource_group_starts_with,
                ends_with_factory=UserUsageBucketConditions.by_resource_group_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.user_uuid is not None:
            condition = self.convert_uuid_filter(
                filter_req.user_uuid,
                equals_factory=UserUsageBucketConditions.by_user_uuid,
                in_factory=UserUsageBucketConditions.by_user_uuids,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.project_id is not None:
            condition = self.convert_uuid_filter(
                filter_req.project_id,
                equals_factory=UserUsageBucketConditions.by_project_id,
                in_factory=UserUsageBucketConditions.by_project_ids,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.domain_name is not None:
            condition = self.convert_string_filter(
                filter_req.domain_name,
                contains_factory=UserUsageBucketConditions.by_domain_name_contains,
                equals_factory=UserUsageBucketConditions.by_domain_name_equals,
                starts_with_factory=UserUsageBucketConditions.by_domain_name_starts_with,
                ends_with_factory=UserUsageBucketConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_req.period_start is not None:
            ps_condition = _build_date_filter_condition(
                filter_req.period_start,
                before_factory=UserUsageBucketConditions.by_period_start_before,
                after_factory=UserUsageBucketConditions.by_period_start_after,
                equals_factory=UserUsageBucketConditions.by_period_start,
                not_equals_factory=UserUsageBucketConditions.by_period_start_not_equals,
            )
            if ps_condition is not None:
                conditions.append(ps_condition)

        if filter_req.period_end is not None:
            pe_condition = _build_date_filter_condition(
                filter_req.period_end,
                before_factory=UserUsageBucketConditions.by_period_end_before,
                after_factory=UserUsageBucketConditions.by_period_end_after,
                equals_factory=UserUsageBucketConditions.by_period_end,
                not_equals_factory=UserUsageBucketConditions.by_period_end_not_equals,
            )
            if pe_condition is not None:
                conditions.append(pe_condition)

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
                result.append(UserUsageBucketOrders.by_period_start(ascending))
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
