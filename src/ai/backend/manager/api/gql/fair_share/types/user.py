"""User Fair Share GQL types, filters, and order-by definitions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

import strawberry
from strawberry import ID, Info
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
    UserFairShareNode,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    UserFairShareOrderField as UserFairShareOrderFieldDTO,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.fair_share.types import UserFairShareData

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
    ResourceSlotGQL,
    ResourceWeightEntryGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


@strawberry.type(
    name="UserFairShare",
    description="Added in 26.1.0. User-level fair share data representing scheduling priority for an individual user. This is the most granular level of fair share calculation.",
)
class UserFairShareGQL(PydanticNodeMixin):
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
        from ai.backend.manager.api.gql.user.types.node import UserV2GQL

        user_data = await info.context.data_loaders.user_loader.load(self.user_uuid)
        if user_data is None:
            return None
        return UserV2GQL.from_data(user_data)

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
        from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL

        domain_data = await info.context.data_loaders.domain_loader.load(self.domain_name)
        if domain_data is None:
            return None
        return DomainV2GQL.from_data(domain_data)

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
        from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL

        project_data = await info.context.data_loaders.project_loader.load(self.project_id)
        if project_data is None:
            return None
        return ProjectV2GQL.from_data(project_data)

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
        from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL

        rg_data = await info.context.data_loaders.resource_group_loader.load(
            self.resource_group_name
        )
        if rg_data is None:
            return None
        return ResourceGroupGQL.from_dataclass(rg_data)

    @classmethod
    def from_dataclass(cls, data: UserFairShareData) -> UserFairShareGQL:
        """Convert UserFairShareData to GraphQL type.

        No async needed - Repository provides complete data.
        Note: metadata can be None for default-generated records.
        """
        return cls(
            id=ID(f"{data.resource_group}:{data.project_id}:{data.user_uuid}"),
            resource_group_name=data.resource_group,
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
                total_decayed_usage=ResourceSlotGQL.from_slot_quantities(
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

    @classmethod
    def from_node(cls, node: UserFairShareNode) -> UserFairShareGQL:
        """Convert UserFairShareNode pydantic DTO to GraphQL type."""
        resource_weights = [
            ResourceWeightEntryGQL(
                resource_type=entry.resource_type,
                weight=Decimal(entry.quantity),
                uses_default=entry.resource_type in node.spec.uses_default_resource_types,
            )
            for entry in node.spec.resource_weights.entries
        ]
        spec = FairShareSpecGQL(
            weight=node.spec.weight,
            uses_default=node.spec.uses_default_weight,
            half_life_days=node.spec.half_life_days,
            lookback_days=node.spec.lookback_days,
            decay_unit_days=node.spec.decay_unit_days,
            resource_weights=resource_weights,
        )
        snapshot = FairShareCalculationSnapshotGQL(
            fair_share_factor=node.calculation_snapshot.fair_share_factor,
            total_decayed_usage=ResourceSlotGQL.from_resource_slot({
                e.resource_type: e.quantity
                for e in node.calculation_snapshot.total_decayed_usage.entries
            }),
            normalized_usage=node.calculation_snapshot.normalized_usage,
            lookback_start=node.calculation_snapshot.lookback_start,
            lookback_end=node.calculation_snapshot.lookback_end,
            last_calculated_at=node.calculation_snapshot.last_calculated_at,
        )
        return cls(
            id=ID(f"{node.resource_group}:{node.user_uuid}:{node.project_id}"),
            resource_group_name=node.resource_group,
            user_uuid=node.user_uuid,
            project_id=node.project_id,
            domain_name=node.domain_name,
            spec=spec,
            calculation_snapshot=snapshot,
            created_at=node.created_at,
            updated_at=node.updated_at,
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


@strawberry.experimental.pydantic.input(
    model=UserFairShareUserNestedFilterDTO,
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

    def to_pydantic(self) -> UserFairShareUserNestedFilterDTO:
        return UserFairShareUserNestedFilterDTO(is_active=self.is_active)


@strawberry.experimental.pydantic.input(
    model=UserFairShareFilterDTO,
    name="UserFairShareFilter",
    description=(
        "Added in 26.1.0. Filter input for querying user fair shares. "
        "Supports filtering by scaling group, user UUID, project ID, and domain name. "
        "This is the most granular level of fair share filtering. "
        "Multiple filters can be combined using AND, OR, and NOT logical operators."
    ),
)
class UserFairShareFilter:
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

    def to_pydantic(self) -> UserFairShareFilterDTO:
        return UserFairShareFilterDTO(
            resource_group=self.resource_group.to_pydantic() if self.resource_group else None,
            user_uuid=self.user_uuid.to_pydantic() if self.user_uuid else None,
            project_id=self.project_id.to_pydantic() if self.project_id else None,
            domain_name=self.domain_name.to_pydantic() if self.domain_name else None,
            user=self.user.to_pydantic() if self.user else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=UserFairShareFilterDTO,
    name="RGUserFairShareFilter",
    description=(
        "Added in 26.2.0. Filter for user fair shares within a resource group scope. "
        "References resource group membership columns to avoid excluding users without fair share records."
    ),
)
class RGUserFairShareFilter:
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

    AND: list[RGUserFairShareFilter] | None = strawberry.field(
        default=None, description="Combine with AND logic."
    )
    OR: list[RGUserFairShareFilter] | None = strawberry.field(
        default=None, description="Combine with OR logic."
    )
    NOT: list[RGUserFairShareFilter] | None = strawberry.field(
        default=None, description="Negate filters."
    )

    def to_pydantic(self) -> UserFairShareFilterDTO:
        return UserFairShareFilterDTO(
            resource_group=self.resource_group.to_pydantic() if self.resource_group else None,
            user_uuid=self.user_uuid.to_pydantic() if self.user_uuid else None,
            project_id=self.project_id.to_pydantic() if self.project_id else None,
            domain_name=self.domain_name.to_pydantic() if self.domain_name else None,
            user=self.user.to_pydantic() if self.user else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


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


@strawberry.experimental.pydantic.input(
    model=UserFairShareOrderDTO,
    name="UserFairShareOrderBy",
    description=(
        "Added in 26.1.0. Specifies ordering for user fair share query results. "
        "Combine field selection with direction to sort results. "
        "Default direction is DESC (descending)."
    ),
)
class UserFairShareOrderBy:
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

    def to_pydantic(self) -> UserFairShareOrderDTO:
        ascending = self.direction == OrderDirection.ASC
        return UserFairShareOrderDTO(
            field=UserFairShareOrderFieldDTO(self.field),
            direction=OrderDirectionDTO.ASC if ascending else OrderDirectionDTO.DESC,
        )


# Mutation Input/Payload Types


@strawberry.experimental.pydantic.input(
    model=UpsertUserFairShareWeightInputDTO,
    name="UpsertUserFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for upserting user fair share weight. "
        "The weight parameter affects scheduling priority - higher weight = higher priority. "
        "Set weight to null to use resource group's default_weight."
    ),
)
class UpsertUserFairShareWeightInput:
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


@strawberry.experimental.pydantic.input(
    model=UserWeightEntryInputDTO,
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


@strawberry.experimental.pydantic.input(
    model=BulkUpsertUserFairShareWeightInputDTO,
    name="BulkUpsertUserFairShareWeightInput",
    description=(
        "Added in 26.1.0. Input for bulk upserting user fair share weights. "
        "Allows updating multiple users in a single transaction."
    ),
)
class BulkUpsertUserFairShareWeightInput:
    """Input for bulk upserting user fair share weights."""

    resource_group_name: str = strawberry.field(
        description="Name of the scaling group (resource group) for all fair shares."
    )
    inputs: list[UserWeightInputItem] = strawberry.field(
        description="List of user weight updates to apply."
    )


@strawberry.experimental.pydantic.type(
    model=BulkUpsertUserFairShareWeightPayloadDTO,
    name="BulkUpsertUserFairShareWeightPayload",
    description="Added in 26.1.0. Payload for bulk user fair share weight upsert mutation.",
    all_fields=True,
)
class BulkUpsertUserFairShareWeightPayload:
    """Payload for bulk user fair share weight upsert mutation."""
