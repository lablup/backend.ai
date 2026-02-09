"""User Fair Share GQL types, filters, and order-by definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.fair_share.types import UserFairShareData
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.fair_share.options import (
    UserFairShareConditions,
    UserFairShareOrders,
)

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
    ResourceSlotGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.user_v2.types.node import UserV2GQL


@strawberry.type(
    name="UserFairShare",
    description="Added in 26.1.0. User-level fair share data representing scheduling priority for an individual user. This is the most granular level of fair share calculation.",
)
class UserFairShareGQL(Node):
    """User-level fair share data with calculated fair share factor."""

    id: NodeID[str]
    resource_group: str = strawberry.field(
        description="Name of the scaling group this fair share belongs to."
    )
    user_uuid: UUID = strawberry.field(
        description="UUID of the user this fair share is calculated for."
    )
    project_id: UUID = strawberry.field(description="UUID of the project the user belongs to.")
    domain_name: str = strawberry.field(description="Name of the domain the user belongs to.")
    spec: FairShareSpecGQL = strawberry.field(
        description="Fair share specification parameters used for calculation."
    )
    calculation_snapshot: FairShareCalculationSnapshotGQL = strawberry.field(
        description="Snapshot of the most recent fair share calculation results."
    )
    created_at: datetime = strawberry.field(description="Timestamp when this record was created.")
    updated_at: datetime = strawberry.field(
        description="Timestamp when this record was last updated."
    )

    @strawberry.field(  # type: ignore[misc]
        description=("Added in 26.2.0. The user entity associated with this fair share record.")
    )
    async def user(
        self,
        info: Info,
    ) -> Annotated[
        UserV2GQL,
        strawberry.lazy("ai.backend.manager.api.gql.user_v2.types.node"),
    ]:
        from ai.backend.manager.api.gql.user_v2.fetcher.user import fetch_user

        return await fetch_user(info=info, user_uuid=self.user_uuid)

    @classmethod
    def from_dataclass(cls, data: UserFairShareData) -> UserFairShareGQL:
        """Convert UserFairShareData to GraphQL type.

        No async needed - Repository provides complete data.
        Note: metadata can be None for default-generated records.
        """
        return cls(
            id=ID(f"{data.resource_group}:{data.project_id}:{data.user_uuid}"),
            resource_group=data.resource_group,
            user_uuid=data.user_uuid,
            project_id=data.project_id,
            domain_name=data.domain_name,
            spec=FairShareSpecGQL.from_spec(
                data.data.spec,
                data.data.use_default,
                data.data.uses_default_resources,
            ),
            calculation_snapshot=FairShareCalculationSnapshotGQL(
                fair_share_factor=data.data.calculation_snapshot.fair_share_factor,
                total_decayed_usage=ResourceSlotGQL.from_resource_slot(
                    data.data.calculation_snapshot.total_decayed_usage
                ),
                normalized_usage=data.data.calculation_snapshot.normalized_usage,
                lookback_start=data.data.calculation_snapshot.lookback_start,
                lookback_end=data.data.calculation_snapshot.lookback_end,
                last_calculated_at=data.data.calculation_snapshot.last_calculated_at,
            ),
            created_at=(
                data.data.metadata.created_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
            updated_at=(
                data.data.metadata.updated_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
        )


UserFairShareEdge = Edge[UserFairShareGQL]


@strawberry.type(
    description=(
        "Added in 26.1.0. Paginated connection for user fair share records. "
        "Provides relay-style cursor-based pagination for efficient traversal of user fair share data. "
        "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
    )
)
class UserFairShareConnection(Connection[UserFairShareGQL]):
    count: int = strawberry.field(
        description="Total number of user fair share records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.input(
    name="UserFairShareUserNestedFilter",
    description=(
        "Added in 26.2.0. Nested filter for user entity fields in user fair share queries. "
        "Allows filtering by user properties such as username, email, and active status."
    ),
)
class UserFairShareUserNestedFilter:
    """Nested filter for user entity within user fair share."""

    username: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by username. Supports equals, contains, startsWith, and endsWith.",
    )
    email: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by email. Supports equals, contains, startsWith, and endsWith.",
    )
    is_active: bool | None = strawberry.field(
        default=None,
        description="Filter by user active status (based on user status field).",
    )

    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if self.username:
            username_condition = self.username.build_query_condition(
                contains_factory=lambda spec: UserFairShareConditions.by_user_username_contains(
                    spec.value
                ),
                equals_factory=lambda spec: UserFairShareConditions.by_user_username_equals(
                    spec.value
                ),
                starts_with_factory=lambda spec: UserFairShareConditions.by_user_username_starts_with(
                    spec.value
                ),
                ends_with_factory=lambda spec: UserFairShareConditions.by_user_username_ends_with(
                    spec.value
                ),
            )
            if username_condition:
                conditions.append(username_condition)
        if self.email:
            email_condition = self.email.build_query_condition(
                contains_factory=lambda spec: UserFairShareConditions.by_user_email_contains(
                    spec.value
                ),
                equals_factory=lambda spec: UserFairShareConditions.by_user_email_equals(
                    spec.value
                ),
                starts_with_factory=lambda spec: UserFairShareConditions.by_user_email_starts_with(
                    spec.value
                ),
                ends_with_factory=lambda spec: UserFairShareConditions.by_user_email_ends_with(
                    spec.value
                ),
            )
            if email_condition:
                conditions.append(email_condition)
        if self.is_active is not None:
            conditions.append(UserFairShareConditions.by_user_is_active(self.is_active))
        return conditions


@strawberry.input(
    name="UserFairShareFilter",
    description=(
        "Added in 26.1.0. Filter input for querying user fair shares. "
        "Supports filtering by scaling group, user UUID, project ID, and domain name. "
        "This is the most granular level of fair share filtering. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class UserFairShareFilter(GQLFilter):
    """Filter for user fair shares."""

    resource_group: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by scaling group name. Scaling groups define resource pool boundaries "
            "where users compete for resources within their project. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    user_uuid: UUIDFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by user UUID. Users are individual accounts that create and run sessions. "
            "Supports equals operation for exact match or 'in' operation for multiple UUIDs."
        ),
    )
    project_id: UUIDFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by project UUID. This filters users by their project membership. "
            "Supports equals operation for exact match or 'in' operation for multiple UUIDs."
        ),
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None,
        description=(
            "Filter by domain name. This filters users belonging to a specific domain. "
            "Supports equals, contains, startsWith, and endsWith operations."
        ),
    )
    user: UserFairShareUserNestedFilter | None = strawberry.field(
        default=None,
        description=(
            "Added in 26.2.0. Nested filter for user entity properties. "
            "Allows filtering by username, email, and active status."
        ),
    )

    AND: list[UserFairShareFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[UserFairShareFilter] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[UserFairShareFilter] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.resource_group:
            sg_condition = self.resource_group.build_query_condition(
                contains_factory=lambda spec: UserFairShareConditions.by_resource_group(spec.value),
                equals_factory=lambda spec: UserFairShareConditions.by_resource_group(spec.value),
                starts_with_factory=lambda spec: UserFairShareConditions.by_resource_group(
                    spec.value
                ),
                ends_with_factory=lambda spec: UserFairShareConditions.by_resource_group(
                    spec.value
                ),
            )
            if sg_condition:
                conditions.append(sg_condition)

        if self.user_uuid:
            uuid_condition = self.user_uuid.build_query_condition(
                equals_factory=lambda spec: UserFairShareConditions.by_user_uuid(spec.value),
                in_factory=lambda spec: UserFairShareConditions.by_user_uuids(spec.values),
            )
            if uuid_condition:
                conditions.append(uuid_condition)

        if self.project_id:
            pid_condition = self.project_id.build_query_condition(
                equals_factory=lambda spec: UserFairShareConditions.by_project_id(spec.value),
                in_factory=lambda spec: UserFairShareConditions.by_project_ids(spec.values),
            )
            if pid_condition:
                conditions.append(pid_condition)

        if self.domain_name:
            dn_condition = self.domain_name.build_query_condition(
                contains_factory=lambda spec: UserFairShareConditions.by_domain_name(spec.value),
                equals_factory=lambda spec: UserFairShareConditions.by_domain_name(spec.value),
                starts_with_factory=lambda spec: UserFairShareConditions.by_domain_name(spec.value),
                ends_with_factory=lambda spec: UserFairShareConditions.by_domain_name(spec.value),
            )
            if dn_condition:
                conditions.append(dn_condition)

        if self.user:
            conditions.extend(self.user.build_conditions())

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


@strawberry.enum(
    name="UserFairShareOrderField",
    description=(
        "Added in 26.1.0. Fields available for ordering user fair share query results. "
        "FAIR_SHARE_FACTOR: Order by the calculated fair share factor (0-1 range, lower = higher priority). "
        "CREATED_AT: Order by record creation timestamp. "
        "USER_USERNAME: Order alphabetically by username (added in 26.2.0). "
        "USER_EMAIL: Order alphabetically by email (added in 26.2.0)."
    ),
)
class UserFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


@strawberry.input(
    name="UserFairShareOrderBy",
    description=(
        "Added in 26.1.0. Specifies ordering for user fair share query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class UserFairShareOrderBy(GQLOrderBy):
    """OrderBy for user fair shares."""

    field: UserFairShareOrderField = strawberry.field(
        description="The field to order by. See UserFairShareOrderField for available options."
    )
    direction: OrderDirection = strawberry.field(
        default=OrderDirection.DESC,
        description=(
            "Sort direction. ASC for ascending (lowest first), DESC for descending (highest first). "
            "For fair_share_factor, ASC shows highest priority users first."
        ),
    )

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case UserFairShareOrderField.FAIR_SHARE_FACTOR:
                return UserFairShareOrders.by_fair_share_factor(ascending)
            case UserFairShareOrderField.CREATED_AT:
                return UserFairShareOrders.by_created_at(ascending)
            case UserFairShareOrderField.USER_USERNAME:
                return UserFairShareOrders.by_user_username(ascending)
            case UserFairShareOrderField.USER_EMAIL:
                return UserFairShareOrders.by_user_email(ascending)


# Mutation Input/Payload Types


@strawberry.input(
    name="UpsertUserFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for upserting user fair share weight. "
        "The weight parameter affects scheduling priority - higher weight = higher priority. "
        "Set weight to null to use resource group's default_weight."
    ),
)
class UpsertUserFairShareWeightInput:
    """Input for upserting user fair share weight."""

    resource_group: str = strawberry.field(
        description="Name of the scaling group (resource group) for this fair share."
    )
    project_id: UUID = strawberry.field(description="UUID of the project the user belongs to.")
    user_uuid: UUID = strawberry.field(description="UUID of the user to update weight for.")
    domain_name: str = strawberry.field(description="Name of the domain the user belongs to.")
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority allocation ratio. "
            "Set to null to use resource group's default_weight."
        ),
    )


@strawberry.type(
    name="UpsertUserFairShareWeightPayload",
    description="Added in 26.1.0. Payload for user fair share weight upsert mutation.",
)
class UpsertUserFairShareWeightPayload:
    """Payload for user fair share weight upsert mutation."""

    user_fair_share: UserFairShareGQL = strawberry.field(
        description="The updated or created user fair share record."
    )


# Bulk Upsert Mutation Input/Payload Types


@strawberry.input(
    name="UserWeightInputItem",
    description=(
        "Added in 26.1.0. Input item for a single user weight in bulk upsert. "
        "Represents one user's weight configuration within a project."
    ),
)
class UserWeightInputItem:
    """Input item for a single user weight in bulk upsert."""

    user_uuid: UUID = strawberry.field(description="UUID of the user to update weight for.")
    project_id: UUID = strawberry.field(
        description="ID of the project this user's fair share belongs to."
    )
    domain_name: str = strawberry.field(description="Name of the domain this project belongs to.")
    weight: Decimal | None = strawberry.field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority allocation ratio. "
            "Set to null to use resource group's default_weight."
        ),
    )


@strawberry.input(
    name="BulkUpsertUserFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for bulk upserting user fair share weights. "
        "Allows updating multiple users in a single transaction."
    ),
)
class BulkUpsertUserFairShareWeightInput:
    """Input for bulk upserting user fair share weights."""

    resource_group: str = strawberry.field(
        description="Name of the scaling group (resource group) for all fair shares."
    )
    inputs: list[UserWeightInputItem] = strawberry.field(
        description="List of user weight updates to apply."
    )


@strawberry.type(
    name="BulkUpsertUserFairShareWeightPayload",
    description="Added in 26.1.0. Payload for bulk user fair share weight upsert mutation.",
)
class BulkUpsertUserFairShareWeightPayload:
    """Payload for bulk user fair share weight upsert mutation."""

    upserted_count: int = strawberry.field(
        description="Number of user fair share records created or updated."
    )
