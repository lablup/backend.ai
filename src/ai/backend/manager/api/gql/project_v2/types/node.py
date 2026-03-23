"""ProjectV2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.fair_share.types import (
    ProjectFairShareScopeDTO,
    ProjectUsageScopeDTO,
)
from ai.backend.common.dto.manager.v2.group.response import ProjectNode
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.fair_share.types import ProjectFairShareGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.resource_slot.overview_types import ActiveResourceOverviewGQL
from ai.backend.manager.api.gql.resource_usage.types import (
    ProjectUsageBucketConnection,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .nested import (
    ProjectBasicInfoGQL,
    ProjectLifecycleInfoGQL,
    ProjectOrganizationInfoGQL,
    ProjectStorageInfoGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.user.types.filters import UserFilterGQL, UserOrderByGQL
    from ai.backend.manager.api.gql.user.types.node import UserV2Connection


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope parameters for filtering project fair shares.", added_version="24.09.0"
    ),
    name="ProjectFairShareScope",
)
class ProjectFairShareScopeGQL(PydanticInputMixin[ProjectFairShareScopeDTO]):
    """Scope parameters for filtering project fair shares."""

    resource_group_name: str = strawberry.field(
        description="Resource group to filter fair shares by."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope parameters for filtering project usage buckets.", added_version="24.09.0"
    ),
    name="ProjectUsageScope",
)
class ProjectUsageScopeGQL(PydanticInputMixin[ProjectUsageScopeDTO]):
    """Scope parameters for filtering project usage buckets."""

    resource_group_name: str = strawberry.field(
        description="Resource group to filter usage buckets by."
    )


@strawberry.federation.type(
    keys=["id"],
    name="ProjectV2",
    description=(
        "Added in 26.2.0. Project entity with structured field groups. "
        "Formerly GroupNode. Provides comprehensive project information organized "
        "into logical categories: basic_info (identity), organization (domain/policy), "
        "storage (vfolders), and lifecycle (status/timestamps). "
        "All fields use typed structures instead of JSON scalars. "
        "Resource allocation and container registry are provided through separate dedicated APIs."
    ),
)
class ProjectV2GQL(PydanticNodeMixin[ProjectNode]):
    """Project entity with structured field groups."""

    id: NodeID[str] = strawberry.field(description="Unique identifier for the project (UUID).")
    basic_info: ProjectBasicInfoGQL = strawberry.field(
        description="Basic project information including name, type, and description."
    )
    organization: ProjectOrganizationInfoGQL = strawberry.field(
        description="Organizational context including domain membership and resource policy."
    )
    storage: ProjectStorageInfoGQL = strawberry.field(
        description="Storage configuration and vfolder host permissions."
    )
    lifecycle: ProjectLifecycleInfoGQL = strawberry.field(
        description="Lifecycle information including activation status and timestamps."
    )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Fair share record for this project in the specified resource group. "
            "Returns the scheduling priority configuration for this project. "
            "Always returns an object, even if no explicit configuration exists "
            "(in which case default values are used)."
        )
    )
    async def fair_share(
        self,
        info: Info,
        scope: ProjectFairShareScopeGQL,
    ) -> ProjectFairShareGQL:
        from ai.backend.common.dto.manager.v2.fair_share.request import GetProjectFairShareInput

        payload = await info.context.adapters.fair_share.get_project(
            GetProjectFairShareInput(
                resource_group=scope.resource_group_name,
                project_id=UUID(str(self.id)),
            )
        )

        return ProjectFairShareGQL.from_pydantic(payload.item)

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Added in 26.4.0. Active resource usage overview for this project. "
            "Returns the currently occupied resource slots and the number of active sessions."
        )
    )
    async def active_resource_overview(
        self,
        info: Info,
    ) -> ActiveResourceOverviewGQL:
        dto = await info.context.adapters.resource_slot.get_project_resource_overview(
            UUID(str(self.id))
        )
        return ActiveResourceOverviewGQL.from_pydantic(dto)

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Usage buckets for this project, filtered by resource group. "
            "Returns aggregated resource usage statistics over time."
        )
    )
    async def usage_buckets(
        self,
        info: Info,
        scope: ProjectUsageScopeGQL,
        filter: ProjectUsageBucketFilter | None = None,
        order_by: list[ProjectUsageBucketOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ProjectUsageBucketConnection:
        from strawberry.relay import PageInfo

        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.resource_usage.types import (
            ProjectUsageBucketEdge,
            ProjectUsageBucketGQL,
        )
        from ai.backend.manager.repositories.resource_usage_history.types import (
            ProjectUsageBucketSearchScope,
        )

        repository_scope = ProjectUsageBucketSearchScope(
            resource_group=scope.resource_group_name,
            domain_name=self.organization.domain_name,
            project_id=UUID(str(self.id)),
        )
        payload = await info.context.adapters.resource_usage.gql_search_project_scoped(
            scope=repository_scope,
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        nodes = [ProjectUsageBucketGQL.from_pydantic(item) for item in payload.items]
        edges = [
            ProjectUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
        ]
        return ProjectUsageBucketConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @strawberry.field(  # type: ignore[misc]
        description="The domain this project belongs to.",
    )
    async def domain(
        self,
        info: Info,
    ) -> Annotated[
        DomainV2GQL,
        strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
    ]:
        from ai.backend.manager.errors.resource import DomainNotFound

        domain: DomainV2GQL | None = await info.context.data_loaders.domain_loader.load(
            self.organization.domain_name
        )
        if domain is None:
            raise DomainNotFound(self.organization.domain_name)
        return domain

    @strawberry.field(  # type: ignore[misc]
        description="Users who are members of this project.",
    )
    async def users(
        self,
        info: Info,
        filter: Annotated[
            UserFilterGQL, strawberry.lazy("ai.backend.manager.api.gql.user.types.filters")
        ]
        | None = None,
        order_by: list[
            Annotated[
                UserOrderByGQL,
                strawberry.lazy("ai.backend.manager.api.gql.user.types.filters"),
            ]
        ]
        | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Annotated[
        UserV2Connection,
        strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
    ]:
        from strawberry.relay import PageInfo

        from ai.backend.common.dto.manager.v2.user.request import AdminSearchUsersInput
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.user.types.node import (
            UserV2Connection,
            UserV2Edge,
            UserV2GQL,
        )
        from ai.backend.manager.repositories.user.types import ProjectUserSearchScope

        repo_scope = ProjectUserSearchScope(project_id=UUID(str(self.id)))
        payload = await info.context.adapters.user.gql_search_by_project(
            scope=repo_scope,
            input=AdminSearchUsersInput(
                filter=filter.to_pydantic() if filter else None,
                order=[o.to_pydantic() for o in order_by] if order_by else None,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            ),
        )
        nodes = [UserV2GQL.from_pydantic(item) for item in payload.items]
        edges = [UserV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return UserV2Connection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.project_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


ProjectV2Edge = Edge[ProjectV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Paginated connection for project records. "
            "Provides relay-style cursor-based pagination for efficient traversal of project data. "
            "Use 'edges' to access individual records with cursor information, "
            "or 'nodes' for direct data access."
        ),
    )
)
class ProjectV2Connection(Connection[ProjectV2GQL]):
    """Paginated connection for project records."""

    count: int = strawberry.field(
        description="Total number of project records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
