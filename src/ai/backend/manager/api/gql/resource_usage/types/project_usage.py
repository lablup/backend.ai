"""Project Usage Bucket GQL types."""

from __future__ import annotations

from typing import Any, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import (
    DateFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.fair_share.types import ResourceSlotGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.resource_usage_history.options import (
    ProjectUsageBucketConditions,
    ProjectUsageBucketOrders,
    UserUsageBucketConditions,
)
from ai.backend.manager.repositories.resource_usage_history.types import (
    ProjectUsageBucketData,
)

from .common import UsageBucketMetadataGQL, UsageBucketOrderField
from .common_calculations import (
    calculate_average_capacity_per_second,
    calculate_average_daily_usage,
    calculate_usage_capacity_ratio,
)
from .user_usage import (
    UserUsageBucketConnection,
    UserUsageBucketFilter,
    UserUsageBucketOrderBy,
)


@strawberry.type(
    name="ProjectUsageBucket",
    description=(
        "Added in 26.1.0. Project-level usage bucket representing aggregated resource "
        "consumption for a specific time period. Usage buckets store historical data "
        "used to calculate fair share factors."
    ),
)
class ProjectUsageBucketGQL(Node):
    """Project-level usage bucket containing aggregated resource usage for a period."""

    id: NodeID[str]
    project_id: UUID = strawberry.field(
        description="UUID of the project this usage bucket belongs to."
    )
    domain_name: str = strawberry.field(description="Name of the domain the project belongs to.")
    resource_group: str = strawberry.field(
        description="Name of the scaling group this usage was recorded in."
    )
    metadata: UsageBucketMetadataGQL = strawberry.field(
        description="Metadata about the usage measurement period and timestamps."
    )
    resource_usage: ResourceSlotGQL = strawberry.field(
        description=(
            "Aggregated resource usage during this period. "
            "Contains the total compute resources consumed by all workloads in this project "
            "during the measurement period (cpu cores, memory bytes, accelerator usage)."
        )
    )
    capacity_snapshot: ResourceSlotGQL = strawberry.field(
        description=(
            "Snapshot of total available capacity in the scaling group at the end of this period. "
            "Used as a reference to calculate relative usage and fair share factors."
        )
    )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.2.0. Average daily resource usage during this period. "
            "Calculated as resource_usage divided by bucket duration in days. "
            "For each resource type, this represents the average amount consumed per day. "
            "Units match the resource type (e.g., CPU cores, memory bytes)."
        )
    )
    def average_daily_usage(self) -> ResourceSlotGQL:
        return calculate_average_daily_usage(
            self.resource_usage,
            self.metadata.period_start,
            self.metadata.period_end,
        )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.2.0. Usage ratio against total available capacity for each resource. "
            "Calculated as resource_usage divided by capacity_snapshot. "
            "Represents the fraction of total capacity consumed (resource-seconds / resource). "
            "The result is in seconds, where 86400 means full utilization for one day. "
            "Values can exceed this if usage exceeds capacity."
        )
    )
    def usage_capacity_ratio(self) -> ResourceSlotGQL:
        return calculate_usage_capacity_ratio(
            self.resource_usage,
            self.capacity_snapshot,
        )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.2.0. Average available capacity per second during this period. "
            "Calculated as capacity_snapshot divided by bucket duration in seconds. "
            "For each resource type, represents the average instantaneous capacity. "
            "Units are resource/second (e.g., CPU cores, memory bytes)."
        )
    )
    def average_capacity_per_second(self) -> ResourceSlotGQL:
        return calculate_average_capacity_per_second(
            self.capacity_snapshot,
            self.metadata.period_start,
            self.metadata.period_end,
        )

    @classmethod
    def from_dataclass(cls, data: ProjectUsageBucketData) -> ProjectUsageBucketGQL:
        return cls(
            id=ID(str(data.id)),
            project_id=data.project_id,
            domain_name=data.domain_name,
            resource_group=data.resource_group,
            metadata=UsageBucketMetadataGQL(
                period_start=data.period_start,
                period_end=data.period_end,
                decay_unit_days=data.decay_unit_days,
                created_at=data.created_at,
                updated_at=data.updated_at,
            ),
            resource_usage=ResourceSlotGQL.from_resource_slot(data.resource_usage),
            capacity_snapshot=ResourceSlotGQL.from_resource_slot(data.capacity_snapshot),
        )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.1.0. User usage buckets belonging to this project. "
            "Returns paginated user-level usage history for all users in this project "
            "within the same scaling group."
        )
    )
    async def user_usage_buckets(
        self,
        info: Info[StrawberryGQLContext],
        filter: UserUsageBucketFilter | None = None,
        order_by: list[UserUsageBucketOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> UserUsageBucketConnection:
        from ai.backend.manager.api.gql.resource_usage.fetcher.user_usage import (
            fetch_user_usage_buckets,
        )

        return await fetch_user_usage_buckets(
            info=info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=[
                UserUsageBucketConditions.by_project_id(self.project_id),
                UserUsageBucketConditions.by_resource_group(self.resource_group),
                UserUsageBucketConditions.by_period_start(self.metadata.period_start),
            ],
        )


ProjectUsageBucketEdge = Edge[ProjectUsageBucketGQL]


@strawberry.type(
    description=(
        "Added in 26.1.0. Paginated connection for project usage bucket records. "
        "Provides relay-style cursor-based pagination for browsing historical usage data by time period. "
        "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
    )
)
class ProjectUsageBucketConnection(Connection[ProjectUsageBucketGQL]):
    count: int = strawberry.field(
        description="Total number of project usage bucket records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.input(
    name="ProjectUsageBucketFilter",
    description=(
        "Added in 26.1.0. Filter input for querying project usage bucket records. "
        "Usage buckets contain historical resource consumption data aggregated by time period for projects. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class ProjectUsageBucketFilter(GQLFilter):
    """Filter for project usage buckets."""

    resource_group: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by scaling group name. Scaling groups define where usage was recorded. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    project_id: UUIDFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by project UUID. This filters usage buckets for a specific project. "
            "Supports equals operation for exact match."
        ),
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by domain name. This filters usage buckets for projects within a specific domain. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    period_start: DateFilter | None = strawberry.field(
        default=None, description="Filter by usage measurement period start date."
    )
    period_end: DateFilter | None = strawberry.field(
        default=None, description="Filter by usage measurement period end date."
    )

    AND: list[ProjectUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[ProjectUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[ProjectUsageBucketFilter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.resource_group:
            sg_condition = self.resource_group.build_query_condition(
                contains_factory=lambda spec: ProjectUsageBucketConditions.by_resource_group(
                    spec.value
                ),
                equals_factory=lambda spec: ProjectUsageBucketConditions.by_resource_group(
                    spec.value
                ),
                starts_with_factory=lambda spec: ProjectUsageBucketConditions.by_resource_group(
                    spec.value
                ),
                ends_with_factory=lambda spec: ProjectUsageBucketConditions.by_resource_group(
                    spec.value
                ),
            )
            if sg_condition:
                conditions.append(sg_condition)

        if self.project_id:
            pid_condition = self.project_id.build_query_condition(
                equals_factory=lambda spec: ProjectUsageBucketConditions.by_project_id(spec.value),
                in_factory=lambda spec: ProjectUsageBucketConditions.by_project_id(spec.values[0]),
            )
            if pid_condition:
                conditions.append(pid_condition)

        if self.domain_name:
            dn_condition = self.domain_name.build_query_condition(
                contains_factory=lambda spec: ProjectUsageBucketConditions.by_domain_name(
                    spec.value
                ),
                equals_factory=lambda spec: ProjectUsageBucketConditions.by_domain_name(spec.value),
                starts_with_factory=lambda spec: ProjectUsageBucketConditions.by_domain_name(
                    spec.value
                ),
                ends_with_factory=lambda spec: ProjectUsageBucketConditions.by_domain_name(
                    spec.value
                ),
            )
            if dn_condition:
                conditions.append(dn_condition)

        if self.period_start:
            ps_condition = self.period_start.build_query_condition(
                before_factory=ProjectUsageBucketConditions.by_period_start_before,
                after_factory=ProjectUsageBucketConditions.by_period_start_after,
                equals_factory=ProjectUsageBucketConditions.by_period_start,
                not_equals_factory=ProjectUsageBucketConditions.by_period_start_not_equals,
            )
            if ps_condition:
                conditions.append(ps_condition)

        if self.period_end:
            pe_condition = self.period_end.build_query_condition(
                before_factory=ProjectUsageBucketConditions.by_period_end_before,
                after_factory=ProjectUsageBucketConditions.by_period_end_after,
                equals_factory=ProjectUsageBucketConditions.by_period_end,
                not_equals_factory=ProjectUsageBucketConditions.by_period_end_not_equals,
            )
            if pe_condition:
                conditions.append(pe_condition)

        if self.AND:
            for sub_filter in self.AND:
                conditions.extend(sub_filter.build_conditions())

        if self.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_conditions.extend(sub_filter.build_conditions())
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))

        if self.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_conditions.extend(sub_filter.build_conditions())
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

        return conditions


@strawberry.input(
    name="ProjectUsageBucketOrderBy",
    description=(
        "Added in 26.1.0. Specifies ordering for project usage bucket query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (most recent first)."
    ),
)
class ProjectUsageBucketOrderBy(GQLOrderBy):
    """OrderBy for project usage buckets."""

    field: UsageBucketOrderField = strawberry.field(
        description="The field to order by. See UsageBucketOrderField for available options."
    )
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description=(
            "Sort direction. ASC for chronological order (oldest first), "
            "DESC for reverse chronological order (most recent first)."
        ),
    )

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case UsageBucketOrderField.PERIOD_START:
                return ProjectUsageBucketOrders.by_period_start(ascending)


__all__ = [
    "ProjectUsageBucketGQL",
    "ProjectUsageBucketConnection",
    "ProjectUsageBucketEdge",
    "ProjectUsageBucketFilter",
    "ProjectUsageBucketOrderBy",
]
