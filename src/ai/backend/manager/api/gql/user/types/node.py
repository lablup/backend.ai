"""User GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self, cast
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.user.response import UserNode
from ai.backend.common.dto.manager.v2.user.types import UserFairShareScope, UserUsageScope
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_federation_type,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.fair_share.types import UserFairShareGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticNodeMixin
from ai.backend.manager.api.gql.resource_usage.types import (
    UserUsageBucketConnection,
    UserUsageBucketFilter,
    UserUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .nested import (
    EntityTimestampsGQL,
    UserBasicInfoGQL,
    UserContainerSettingsGQL,
    UserOrganizationInfoGQL,
    UserSecurityInfoGQL,
    UserStatusInfoGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.project_v2.types.filters import (
        ProjectV2Filter,
        ProjectV2OrderBy,
    )
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2Connection


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope parameters for filtering user fair shares.", added_version="24.09.0"
    ),
    name="UserFairShareScope",
)
class UserFairShareScopeGQL(PydanticInputMixin[UserFairShareScope]):
    """Scope parameters for filtering user fair shares."""

    resource_group_name: str = gql_field(description="Resource group to filter fair shares by.")
    project_id: UUID = gql_field(
        description="Project ID that the user belongs to (required for user-level fair shares)."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope parameters for filtering user usage buckets.", added_version="24.09.0"
    ),
    name="UserUsageScope",
)
class UserUsageScopeGQL(PydanticInputMixin[UserUsageScope]):
    """Scope parameters for filtering user usage buckets."""

    resource_group_name: str = gql_field(description="Resource group to filter usage buckets by.")
    project_id: UUID = gql_field(
        description="Project ID that the user belongs to (required for user-level usage)."
    )


@gql_federation_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "User entity with structured field groups. "
            "Provides comprehensive user information organized into logical categories: "
            "basic_info (profile), status (account state), organization (permissions), "
            "security (auth settings), container (execution settings), and timestamps."
        ),
    ),
    name="UserV2",
    keys=["id"],
)
class UserV2GQL(PydanticNodeMixin[UserNode]):
    """User entity with structured field groups."""

    id: NodeID[str] = gql_field(description="Unique identifier for the user (UUID).")
    basic_info: UserBasicInfoGQL = gql_field(
        description="Basic profile information including username, email, and display name."
    )
    status: UserStatusInfoGQL = gql_field(description="Account status and password-related flags.")
    organization: UserOrganizationInfoGQL = gql_field(
        description="Organizational context including domain, role, and resource policy."
    )
    security: UserSecurityInfoGQL = gql_field(
        description="Security settings including IP restrictions and TOTP configuration."
    )
    container: UserContainerSettingsGQL = gql_field(
        description="Container execution settings including UID/GID mappings."
    )
    timestamps: EntityTimestampsGQL = gql_field(description="Creation and modification timestamps.")

    @gql_field(
        description="Fair share record for this user in the specified resource group and project. Returns the scheduling priority configuration for this user. Always returns an object, even if no explicit configuration exists (in which case default values are used)."
    )  # type: ignore[misc]
    async def fair_share(
        self,
        info: Info,
        scope: UserFairShareScopeGQL,
    ) -> UserFairShareGQL:
        from ai.backend.common.dto.manager.v2.fair_share.request import GetUserFairShareInput

        if self.organization.domain_name is None:
            raise InvalidAPIParameters("User must belong to a domain to query fair share")

        payload = await info.context.adapters.fair_share.get_user(
            GetUserFairShareInput(
                resource_group=scope.resource_group_name,
                project_id=scope.project_id,
                user_uuid=UUID(str(self.id)),
            )
        )

        return UserFairShareGQL.from_pydantic(payload.item)

    @gql_field(
        description="Usage buckets for this user, filtered by resource group and project. Returns aggregated resource usage statistics over time."
    )  # type: ignore[misc]
    async def usage_buckets(
        self,
        info: Info,
        scope: UserUsageScopeGQL,
        filter: UserUsageBucketFilter | None = None,
        order_by: list[UserUsageBucketOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> UserUsageBucketConnection:
        from strawberry.relay import PageInfo

        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.resource_usage.types import (
            UserUsageBucketEdge,
            UserUsageBucketGQL,
        )
        from ai.backend.manager.repositories.resource_usage_history.types import (
            UserUsageBucketSearchScope,
        )

        if self.organization.domain_name is None:
            raise InvalidAPIParameters("User must belong to a domain to query usage buckets")
        repository_scope = UserUsageBucketSearchScope(
            resource_group=scope.resource_group_name,
            domain_name=self.organization.domain_name,
            project_id=scope.project_id,
            user_uuid=UUID(str(self.id)),
        )
        payload = await info.context.adapters.resource_usage.gql_search_user_scoped(
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
        nodes = [UserUsageBucketGQL.from_pydantic(item) for item in payload.items]
        edges = [
            UserUsageBucketEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
        ]
        return UserUsageBucketConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=payload.has_next_page,
                has_previous_page=payload.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=payload.total_count,
        )

    @gql_field(description="The domain this user belongs to.")  # type: ignore[misc]
    async def domain(
        self,
        info: Info,
    ) -> (
        Annotated[
            DomainV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
        ]
        | None
    ):
        if self.organization.domain_name is None:
            return None
        domain: DomainV2GQL | None = await info.context.data_loaders.domain_loader.load(
            self.organization.domain_name
        )
        return domain

    @gql_field(description="Projects this user is a member of.")  # type: ignore[misc]
    async def projects(
        self,
        info: Info,
        filter: Annotated[
            ProjectV2Filter,
            strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.filters"),
        ]
        | None = None,
        order_by: list[
            Annotated[
                ProjectV2OrderBy,
                strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.filters"),
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
        ProjectV2Connection,
        strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.node"),
    ]:
        from strawberry.relay import PageInfo

        from ai.backend.common.dto.manager.v2.group.request import AdminSearchProjectsInput
        from ai.backend.manager.api.gql.base import encode_cursor
        from ai.backend.manager.api.gql.project_v2.types.node import (
            ProjectV2Connection,
            ProjectV2Edge,
            ProjectV2GQL,
        )
        from ai.backend.manager.repositories.group.types import UserProjectSearchScope

        scope = UserProjectSearchScope(user_uuid=UUID(str(self.id)))
        payload = await info.context.adapters.project.search_by_user(
            scope=scope,
            input=AdminSearchProjectsInput(
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
        nodes = [ProjectV2GQL.from_pydantic(node) for node in payload.items]
        edges = [ProjectV2Edge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
        return ProjectV2Connection(
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
        results = await info.context.data_loaders.user_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


UserV2Edge = Edge[UserV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Paginated connection for user records. "
            "Provides relay-style cursor-based pagination for efficient traversal of user data. "
            "Use 'edges' to access individual records with cursor information, "
            "or 'nodes' for direct data access."
        ),
    )
)
class UserV2Connection(Connection[UserV2GQL]):
    """Paginated connection for user records."""

    count: int = gql_field(description="Total number of user records matching the query criteria.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
