"""Project Fair Share GQL types, filters, and order-by definitions."""

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
    BulkUpsertProjectFairShareWeightInput as BulkUpsertProjectFairShareWeightInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    ProjectFairShareFilter as ProjectFairShareFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    ProjectFairShareOrder as ProjectFairShareOrderDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    ProjectFairShareProjectNestedFilter as ProjectFairShareProjectNestedFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    ProjectWeightEntryInput as ProjectWeightEntryInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UpsertProjectFairShareWeightInput as UpsertProjectFairShareWeightInputDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertProjectFairShareWeightPayload as BulkUpsertProjectFairShareWeightPayloadDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    ProjectFairShareNode,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    UpsertProjectFairShareWeightPayload as UpsertProjectFairShareWeightPayloadDTO,
)
from ai.backend.common.dto.manager.v2.group.types import ProjectTypeFilter
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, UUIDFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
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


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Project-level fair share data representing scheduling priority for a specific project. The fair share factor determines resource allocation relative to other projects in the same domain.",
    ),
    name="ProjectFairShare",
)
class ProjectFairShareGQL(PydanticNodeMixin[ProjectFairShareNode]):
    """Project-level fair share data with calculated fair share factor."""

    id: NodeID[str]
    resource_group_name: str = gql_field(
        description="Name of the scaling group this fair share belongs to."
    )
    project_id: UUID = gql_field(
        description="UUID of the project this fair share is calculated for."
    )
    domain_name: str = gql_field(description="Name of the domain the project belongs to.")
    spec: FairShareSpecGQL = gql_field(
        description="Fair share specification parameters used for calculation."
    )
    calculation_snapshot: FairShareCalculationSnapshotGQL = gql_field(
        description="Snapshot of the most recent fair share calculation results."
    )
    created_at: datetime = gql_field(description="Timestamp when this record was created.")
    updated_at: datetime = gql_field(description="Timestamp when this record was last updated.")

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="The project entity associated with this fair share record.",
        )
    )  # type: ignore[misc]
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

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="The domain entity associated with this fair share record.",
        )
    )  # type: ignore[misc]
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

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="The resource group associated with this fair share record.",
        )
    )  # type: ignore[misc]
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


ProjectFairShareEdge = Edge[ProjectFairShareGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Paginated connection for project fair share records. "
            "Provides relay-style cursor-based pagination for efficient traversal of project fair share data. "
            "Use 'edges' to access individual records with cursor information, or 'nodes' for direct data access."
        ),
    )
)
class ProjectFairShareConnection(Connection[ProjectFairShareGQL]):
    count: int = gql_field(
        description="Total number of project fair share records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0", description="Project type enum for fair share filtering."
    ),
    name="ProjectFairShareTypeEnum",
)
class ProjectFairShareTypeEnum(StrEnum):
    """Project type enum for fair share context."""

    GENERAL = "general"
    MODEL_STORE = "model-store"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for project type enum in fair share queries. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    name="ProjectFairShareTypeEnumFilter",
)
class ProjectFairShareTypeEnumFilter(PydanticInputMixin[ProjectTypeFilter]):
    """Filter for project type enum fields in fair share context."""

    equals: ProjectFairShareTypeEnum | None = gql_field(
        description="Exact match for project type.", default=None
    )
    in_: list[ProjectFairShareTypeEnum] | None = gql_field(
        description="Match any of the provided types.", name="in", default=None
    )
    not_equals: ProjectFairShareTypeEnum | None = gql_field(
        description="Exclude exact type match.", default=None
    )
    not_in: list[ProjectFairShareTypeEnum] | None = gql_field(
        description="Exclude any of the provided types.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for project entity fields in project fair share queries. Allows filtering by project properties such as name, active status, and type.",
        added_version="26.2.0",
    ),
    name="ProjectFairShareProjectNestedFilter",
)
class ProjectFairShareProjectNestedFilter(
    PydanticInputMixin[ProjectFairShareProjectNestedFilterDTO]
):
    """Nested filter for project entity within project fair share."""

    name: StringFilter | None = gql_field(
        description="Filter by project name. Supports equals, contains, startsWith, and endsWith.",
        default=None,
    )
    is_active: bool | None = gql_field(description="Filter by project active status.", default=None)
    type: ProjectFairShareTypeEnumFilter | None = gql_field(
        description="Filter by project type (GENERAL, MODEL_STORE).", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying project fair shares. Supports filtering by scaling group, project ID, and domain name. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.1.0",
    ),
    name="ProjectFairShareFilter",
)
class ProjectFairShareFilter(PydanticInputMixin[ProjectFairShareFilterDTO]):
    """Filter for project fair shares."""

    resource_group: StringFilter | None = gql_field(
        description="Filter by scaling group name. Scaling groups define resource pool boundaries where projects compete for resources within their domain. Supports equals, contains, startsWith, and endsWith operations.",
        default=None,
    )
    project_id: UUIDFilter | None = gql_field(
        description="Filter by project UUID. Projects are containers for sessions and user activities. Supports equals operation for exact match or 'in' operation for multiple UUIDs.",
        default=None,
    )
    domain_name: StringFilter | None = gql_field(
        description="Filter by domain name. This filters projects belonging to a specific domain. Supports equals, contains, startsWith, and endsWith operations.",
        default=None,
    )
    project: ProjectFairShareProjectNestedFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.2.0",
            description="Nested filter for project entity properties. Allows filtering by project name, active status, and type.",
        ),
        default=None,
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
        description="Filter for project fair shares within a resource group scope. References resource group membership columns to avoid excluding projects without fair share records.",
        added_version="26.2.0",
    ),
    name="RGProjectFairShareFilter",
)
class RGProjectFairShareFilter(PydanticInputMixin[ProjectFairShareFilterDTO]):
    """Filter for project fair shares in RG context (uses INNER JOIN'd columns)."""

    resource_group: StringFilter | None = gql_field(
        description="Filter by scaling group name.", default=None
    )
    project_id: UUIDFilter | None = gql_field(description="Filter by project UUID.", default=None)
    domain_name: StringFilter | None = gql_field(description="Filter by domain name.", default=None)
    project: ProjectFairShareProjectNestedFilter | None = gql_field(
        description="Filter by project properties.", default=None
    )

    AND: list[Self] | None = gql_field(description="Combine with AND logic.", default=None)
    OR: list[Self] | None = gql_field(description="Combine with OR logic.", default=None)
    NOT: list[Self] | None = gql_field(description="Negate filters.", default=None)


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Fields available for ordering project fair share query results. "
            "FAIR_SHARE_FACTOR: Order by the calculated fair share factor (0-1 range, lower = higher priority). "
            "CREATED_AT: Order by record creation timestamp. "
            "PROJECT_NAME: Order alphabetically by project name. "
            "PROJECT_IS_ACTIVE: Order by project active status."
        ),
    ),
    name="ProjectFairShareOrderField",
)
class ProjectFairShareOrderField(StrEnum):
    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"
    PROJECT_NAME = "project_name"
    PROJECT_IS_ACTIVE = "project_is_active"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for project fair share query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.1.0",
    ),
    name="ProjectFairShareOrderBy",
)
class ProjectFairShareOrderBy(PydanticInputMixin[ProjectFairShareOrderDTO]):
    """OrderBy for project fair shares."""

    field: ProjectFairShareOrderField = gql_field(
        description="The field to order by. See ProjectFairShareOrderField for available options."
    )
    direction: OrderDirection = gql_field(
        description="Sort direction. ASC for ascending (lowest first), DESC for descending (highest first). For fair_share_factor, ASC shows highest priority projects first.",
        default=OrderDirection.DESC,
    )


# Mutation Input/Payload Types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for upserting project fair share weight. The weight parameter affects scheduling priority - higher weight = higher priority. Set weight to null to use resource group's default_weight.",
        added_version="26.1.0",
    ),
    name="UpsertProjectFairShareWeightInput",
)
class UpsertProjectFairShareWeightInput(PydanticInputMixin[UpsertProjectFairShareWeightInputDTO]):
    """Input for upserting project fair share weight."""

    resource_group_name: str = gql_field(
        description="Name of the scaling group (resource group) for this fair share."
    )
    project_id: UUID = gql_field(description="UUID of the project to update weight for.")
    domain_name: str = gql_field(description="Name of the domain the project belongs to.")
    weight: Decimal | None = gql_field(
        description="Priority weight multiplier. Higher weight = higher priority allocation ratio. Set to null to use resource group's default_weight.",
        default=None,
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for project fair share weight upsert mutation.",
    ),
    model=UpsertProjectFairShareWeightPayloadDTO,
    name="UpsertProjectFairShareWeightPayload",
)
class UpsertProjectFairShareWeightPayload(
    PydanticOutputMixin[UpsertProjectFairShareWeightPayloadDTO]
):
    """Payload for project fair share weight upsert mutation."""

    project_fair_share: ProjectFairShareGQL = gql_field(
        description="The updated or created project fair share record."
    )


# Bulk Upsert Mutation Input/Payload Types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input item for a single project weight in bulk upsert. Represents one project's weight configuration.",
        added_version="26.1.0",
    ),
    name="ProjectWeightInputItem",
)
class ProjectWeightInputItem(PydanticInputMixin[ProjectWeightEntryInputDTO]):
    """Input item for a single project weight in bulk upsert."""

    project_id: UUID = gql_field(description="ID of the project to update weight for.")
    domain_name: str = gql_field(description="Name of the domain this project belongs to.")
    weight: Decimal | None = gql_field(
        description="Priority weight multiplier. Higher weight = higher priority allocation ratio. Set to null to use resource group's default_weight.",
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk upserting project fair share weights. Allows updating multiple projects in a single transaction.",
        added_version="26.1.0",
    ),
    name="BulkUpsertProjectFairShareWeightInput",
)
class BulkUpsertProjectFairShareWeightInput(
    PydanticInputMixin[BulkUpsertProjectFairShareWeightInputDTO]
):
    """Input for bulk upserting project fair share weights."""

    resource_group_name: str = gql_field(
        description="Name of the scaling group (resource group) for all fair shares."
    )
    inputs: list[ProjectWeightInputItem] = gql_field(
        description="List of project weight updates to apply."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="Payload for bulk project fair share weight upsert mutation.",
    ),
    model=BulkUpsertProjectFairShareWeightPayloadDTO,
    all_fields=True,
    name="BulkUpsertProjectFairShareWeightPayload",
)
class BulkUpsertProjectFairShareWeightPayload(
    PydanticOutputMixin[BulkUpsertProjectFairShareWeightPayloadDTO]
):
    pass
