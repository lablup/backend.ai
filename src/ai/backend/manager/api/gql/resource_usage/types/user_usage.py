"""User Usage Bucket GQL types."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_usage.request import (
    UserUsageBucketFilter as UserUsageBucketFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.request import (
    UserUsageBucketOrderBy as UserUsageBucketOrderByDTO,
)
from ai.backend.common.dto.manager.v2.resource_usage.response import (
    UserUsageBucketNode,
)
from ai.backend.manager.api.gql.base import (
    DateFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.fair_share.types import ResourceSlotGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy

from .common import UsageBucketMetadataGQL, UsageBucketOrderField
from .common_calculations import (
    calculate_average_daily_usage,
    calculate_usage_capacity_ratio,
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "User-level usage bucket representing aggregated resource "
            "consumption for a specific time period. This is the most granular level of usage tracking."
        ),
    ),
    name="UserUsageBucket",
)
class UserUsageBucketGQL(PydanticNodeMixin[UserUsageBucketNode]):
    """User-level usage bucket containing aggregated resource usage for a period."""

    id: NodeID[str]
    user_uuid: UUID = gql_field(description="UUID of the user this usage bucket belongs to.")
    project_id: UUID = gql_field(description="UUID of the project the user belongs to.")
    domain_name: str = gql_field(description="Name of the domain the user belongs to.")
    resource_group_name: str = gql_field(
        description="Name of the scaling group this usage was recorded in."
    )
    metadata: UsageBucketMetadataGQL = gql_field(
        description="Metadata about the usage measurement period and timestamps."
    )
    resource_usage: ResourceSlotGQL = gql_field(
        description="Aggregated resource usage during this period. Contains the total compute resources consumed by this user's workloads during the measurement period (cpu cores, memory bytes, accelerator usage)."
    )
    capacity_snapshot: ResourceSlotGQL = gql_field(
        description="Snapshot of total available capacity in the scaling group at the end of this period. Used as a reference to calculate relative usage and fair share factors."
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Average daily resource usage during this period. Calculated as resource_usage divided by bucket duration in days. For each resource type, this represents the average amount consumed per day. Units match the resource type (e.g., CPU cores, memory bytes).",
        )
    )  # type: ignore[misc]
    def average_daily_usage(self) -> ResourceSlotGQL:
        return calculate_average_daily_usage(
            self.resource_usage,
            self.metadata.period_start,
            self.metadata.period_end,
        )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Usage ratio against total available capacity for each resource. Calculated as resource_usage divided by capacity_snapshot. Represents the fraction of total capacity consumed (resource-seconds / resource). The result is in seconds, where 86400 means full utilization for one day. Values can exceed this if usage exceeds capacity.",
        )
    )  # type: ignore[misc]
    def usage_capacity_ratio(self) -> ResourceSlotGQL:
        return calculate_usage_capacity_ratio(
            self.resource_usage,
            self.capacity_snapshot,
        )


UserUsageBucketEdge = Edge[UserUsageBucketGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Paginated connection for user usage bucket records. "
            "Provides relay-style cursor-based pagination for browsing historical usage data by time period. "
            "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
        ),
    ),
)
class UserUsageBucketConnection(Connection[UserUsageBucketGQL]):
    count: int = gql_field(
        description="Total number of user usage bucket records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying user usage bucket records. Usage buckets contain historical resource consumption data aggregated by time period for users. This is the most granular level of usage bucket filtering. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.1.0",
    ),
    name="UserUsageBucketFilter",
)
class UserUsageBucketFilter(PydanticInputMixin[UserUsageBucketFilterDTO], GQLFilter):
    """Filter for user usage buckets."""

    resource_group: StringFilter | None = gql_field(
        description="Filter by scaling group name. Scaling groups define where usage was recorded. Supports equals, contains, startsWith, and endsWith operations.",
        default=None,
    )
    user_uuid: UUIDFilter | None = gql_field(
        description="Filter by user UUID. This filters usage buckets for a specific user. Supports equals operation for exact match.",
        default=None,
    )
    project_id: UUIDFilter | None = gql_field(
        description="Filter by project UUID. This filters usage buckets for users within a specific project. Supports equals operation for exact match.",
        default=None,
    )
    domain_name: StringFilter | None = gql_field(
        description="Filter by domain name. This filters usage buckets for users within a specific domain. Supports equals, contains, startsWith, and endsWith operations.",
        default=None,
    )
    period_start: DateFilter | None = gql_field(
        description="Filter by usage measurement period start date.", default=None
    )
    period_end: DateFilter | None = gql_field(
        description="Filter by usage measurement period end date.", default=None
    )

    AND: list[Self] | None = gql_field(
        description="Combine multiple filters with AND logic. All conditions must match.",
        default=None,
    )
    OR: list[Self] | None = gql_field(
        description="Combine multiple filters with OR logic. At least one condition must match.",
        default=None,
    )
    NOT: list[Self] | None = gql_field(
        description="Negate the specified filters. Records matching these conditions will be excluded.",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for user usage bucket query results. Combine field selection with direction to sort results. Default direction is DESC (most recent first).",
        added_version="26.1.0",
    ),
    name="UserUsageBucketOrderBy",
)
class UserUsageBucketOrderBy(PydanticInputMixin[UserUsageBucketOrderByDTO], GQLOrderBy):
    """OrderBy for user usage buckets."""

    field: UsageBucketOrderField = gql_field(
        description="The field to order by. See UsageBucketOrderField for available options."
    )
    direction: OrderDirection = gql_field(
        description="Sort direction. ASC for chronological order (oldest first), DESC for reverse chronological order (most recent first).",
        default=OrderDirection.DESC,
    )


__all__ = [
    "UserUsageBucketGQL",
    "UserUsageBucketConnection",
    "UserUsageBucketEdge",
    "UserUsageBucketFilter",
    "UserUsageBucketOrderBy",
]
