"""User Fair Share GQL types, filters, and order-by definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.fair_share.request import (
    BulkUpsertUserFairShareWeightInput as BulkUpsertUserFairShareWeightInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UpsertUserFairShareWeightInput as UpsertUserFairShareWeightInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UserFairShareFilter as UserFairShareFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UserFairShareOrder as UserFairShareOrderDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UserFairShareUserNestedFilter as UserFairShareUserNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UserWeightEntryInput as UserWeightEntryInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertUserFairShareWeightPayload as BulkUpsertUserFairShareWeightPayloadDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    UpsertUserFairShareWeightPayload as UpsertUserFairShareWeightPayloadDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    UserFairShareNode,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="User-level fair share data representing scheduling priority for an individual user. This is the most granular level of fair share calculation.",
    ),
    name="UserFairShare",
)
class UserFairShareGQL(PydanticNodeMixin[UserFairShareNode]):
    """User-level fair share data with calculated fair share factor."""

    id: NodeID[str]
    resource_group_name: str = strawberry.field(
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
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        user_data = await info.context.data_loaders.user_loader.load(self.user_uuid)
        if user_data is None:
            return None
        return user_data

    @strawberry.field(  # type: ignore[misc]
        description=("Added in 26.2.0. The domain entity associated with this fair share record."),
    )
    async def domain(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            DomainV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.domain_loader.load(self.domain_name)

    @strawberry.field(  # type: ignore[misc]
        description=("Added in 26.2.0. The project entity associated with this fair share record."),
    )
    async def project(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ProjectV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.node"),
        ]
        | None
    ):
        project_data = await info.context.data_loaders.project_loader.load(self.project_id)
        if project_data is None:
            return None
        return project_data

    @strawberry.field(  # type: ignore[misc]
        description=("Added in 26.2.0. The resource group associated with this fair share record."),
    )
    async def resource_group(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ResourceGroupGQL,
            strawberry.lazy("ai.backend.manager.api.gql.resource_group.types"),
        ]
        | None
    ):
        return await info.context.data_loaders.resource_group_loader.load(self.resource_group_name)


UserFairShareEdge = Edge[UserFairShareGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Paginated connection for user fair share records. "
            "Provides relay-style cursor-based pagination for efficient traversal of user fair share data. "
            "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
        ),
    )
)
class UserFairShareConnection(Connection[UserFairShareGQL]):
    count: int = strawberry.field(
        description="Total number of user fair share records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for user entity fields in user fair share queries. Allows filtering by user properties such as username, email, and active status.",
        added_version="26.2.0",
    ),
    name="UserFairShareUserNestedFilter",
)
class UserFairShareUserNestedFilter(PydanticInputMixin[UserFairShareUserNestedFilterDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying user fair shares. Supports filtering by scaling group, user UUID, project ID, and domain name. This is the most granular level of fair share filtering. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.1.0",
    ),
    name="UserFairShareFilter",
)
class UserFairShareFilter(PydanticInputMixin[UserFairShareFilterDTO]):
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

    AND: list[Self] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with AND logic. All conditions must match.",
    )
    OR: list[Self] | None = strawberry.field(
        default=None,
        description="Combine multiple filters with OR logic. At least one condition must match.",
    )
    NOT: list[Self] | None = strawberry.field(
        default=None,
        description="Negate the specified filters. Records matching these conditions will be excluded.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for user fair shares within a resource group scope. References resource group membership columns to avoid excluding users without fair share records.",
        added_version="26.2.0",
    ),
    name="RGUserFairShareFilter",
)
class RGUserFairShareFilter(PydanticInputMixin[UserFairShareFilterDTO]):
    """Filter for user fair shares in RG context (uses INNER JOIN'd columns)."""

    resource_group: StringFilter | None = strawberry.field(
        default=None, description="Filter by scaling group name."
    )
    user_uuid: UUIDFilter | None = strawberry.field(
        default=None, description="Filter by user UUID."
    )
    project_id: UUIDFilter | None = strawberry.field(
        default=None, description="Filter by project UUID."
    )
    domain_name: StringFilter | None = strawberry.field(
        default=None, description="Filter by domain name."
    )
    user: UserFairShareUserNestedFilter | None = strawberry.field(
        default=None, description="Filter by user properties."
    )

    AND: list[Self] | None = strawberry.field(default=None, description="Combine with AND logic.")
    OR: list[Self] | None = strawberry.field(default=None, description="Combine with OR logic.")
    NOT: list[Self] | None = strawberry.field(default=None, description="Negate filters.")


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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for user fair share query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.1.0",
    ),
    name="UserFairShareOrderBy",
)
class UserFairShareOrderBy(PydanticInputMixin[UserFairShareOrderDTO]):
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


# Mutation Input/Payload Types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for upserting user fair share weight. The weight parameter affects scheduling priority - higher weight = higher priority. Set weight to null to use resource group's default_weight.",
        added_version="26.1.0",
    ),
    name="UpsertUserFairShareWeightInput",
)
class UpsertUserFairShareWeightInput(PydanticInputMixin[UpsertUserFairShareWeightInputDTO]):
    """Input for upserting user fair share weight."""

    resource_group_name: str = strawberry.field(
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for user fair share weight upsert mutation.",
    ),
    model=UpsertUserFairShareWeightPayloadDTO,
    name="UpsertUserFairShareWeightPayload",
)
class UpsertUserFairShareWeightPayload(PydanticOutputMixin[UpsertUserFairShareWeightPayloadDTO]):
    """Payload for user fair share weight upsert mutation."""

    user_fair_share: UserFairShareGQL = strawberry.field(
        description="The updated or created user fair share record."
    )


# Bulk Upsert Mutation Input/Payload Types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input item for a single user weight in bulk upsert. Represents one user's weight configuration within a project.",
        added_version="26.1.0",
    ),
    name="UserWeightInputItem",
)
class UserWeightInputItem(PydanticInputMixin[UserWeightEntryInputDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk upserting user fair share weights. Allows updating multiple users in a single transaction.",
        added_version="26.1.0",
    ),
    name="BulkUpsertUserFairShareWeightInput",
)
class BulkUpsertUserFairShareWeightInput(PydanticInputMixin[BulkUpsertUserFairShareWeightInputDTO]):
    """Input for bulk upserting user fair share weights."""

    resource_group_name: str = strawberry.field(
        description="Name of the scaling group (resource group) for all fair shares."
    )
    inputs: list[UserWeightInputItem] = strawberry.field(
        description="List of user weight updates to apply."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for bulk user fair share weight upsert mutation.",
    ),
    model=BulkUpsertUserFairShareWeightPayloadDTO,
    all_fields=True,
    name="BulkUpsertUserFairShareWeightPayload",
)
class BulkUpsertUserFairShareWeightPayload(
    PydanticOutputMixin[BulkUpsertUserFairShareWeightPayloadDTO]
):
    pass
