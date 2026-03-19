"""User GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.user.response import UserNode
from ai.backend.common.dto.manager.v2.user.types import UserFairShareScope, UserUsageScope
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.gql.fair_share.types import UserFairShareGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.resource_usage.types import (
    UserUsageBucketConnection,
    UserUsageBucketFilter,
    UserUsageBucketOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .enums import UserRoleEnumGQL, UserStatusEnumGQL
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
    from ai.backend.manager.data.user.types import UserData


@strawberry.experimental.pydantic.input(
    model=UserFairShareScope,
    name="UserFairShareScope",
    description="Scope parameters for filtering user fair shares.",
)
class UserFairShareScopeGQL:
    """Scope parameters for filtering user fair shares."""

    resource_group_name: str = strawberry.field(
        description="Resource group to filter fair shares by."
    )
    project_id: UUID = strawberry.field(
        description="Project ID that the user belongs to (required for user-level fair shares)."
    )

    def to_pydantic(self) -> UserFairShareScope:
        return UserFairShareScope(
            resource_group_name=self.resource_group_name,
            project_id=self.project_id,
        )


@strawberry.experimental.pydantic.input(
    model=UserUsageScope,
    name="UserUsageScope",
    description="Scope parameters for filtering user usage buckets.",
)
class UserUsageScopeGQL:
    """Scope parameters for filtering user usage buckets."""

    resource_group_name: str = strawberry.field(
        description="Resource group to filter usage buckets by."
    )
    project_id: UUID = strawberry.field(
        description="Project ID that the user belongs to (required for user-level usage)."
    )

    def to_pydantic(self) -> UserUsageScope:
        return UserUsageScope(
            resource_group_name=self.resource_group_name,
            project_id=self.project_id,
        )


@strawberry.federation.type(
    keys=["id"],
    name="UserV2",
    description=(
        "Added in 26.2.0. User entity with structured field groups. "
        "Provides comprehensive user information organized into logical categories: "
        "basic_info (profile), status (account state), organization (permissions), "
        "security (auth settings), container (execution settings), and timestamps."
    ),
)
class UserV2GQL(PydanticNodeMixin):
    """User entity with structured field groups."""

    id: NodeID[str] = strawberry.field(description="Unique identifier for the user (UUID).")
    basic_info: UserBasicInfoGQL = strawberry.field(
        description="Basic profile information including username, email, and display name."
    )
    status: UserStatusInfoGQL = strawberry.field(
        description="Account status and password-related flags."
    )
    organization: UserOrganizationInfoGQL = strawberry.field(
        description="Organizational context including domain, role, and resource policy."
    )
    security: UserSecurityInfoGQL = strawberry.field(
        description="Security settings including IP restrictions and TOTP configuration."
    )
    container: UserContainerSettingsGQL = strawberry.field(
        description="Container execution settings including UID/GID mappings."
    )
    timestamps: EntityTimestampsGQL = strawberry.field(
        description="Creation and modification timestamps."
    )

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Fair share record for this user in the specified resource group and project. "
            "Returns the scheduling priority configuration for this user. "
            "Always returns an object, even if no explicit configuration exists "
            "(in which case default values are used)."
        )
    )
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

        return UserFairShareGQL.from_node(payload.item)

    @strawberry.field(  # type: ignore[misc]
        description=(
            "Usage buckets for this user, filtered by resource group and project. "
            "Returns aggregated resource usage statistics over time."
        )
    )
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
        nodes = [UserUsageBucketGQL.from_node(item) for item in payload.items]
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

    @strawberry.field(  # type: ignore[misc]
        description="The domain this user belongs to.",
    )
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
        from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL

        if self.organization.domain_name is None:
            return None
        data = await info.context.data_loaders.domain_loader.load(self.organization.domain_name)
        if data is None:
            return None
        return DomainV2GQL.from_data(data)

    @strawberry.field(  # type: ignore[misc]
        description="Projects this user is a member of.",
    )
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

        from ai.backend.common.dto.manager.v2.group.request import AdminSearchGroupsInput
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
            input=AdminSearchGroupsInput(
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
        nodes = [ProjectV2GQL.from_node(node) for node in payload.items]
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
        return [cls.from_data(data) if data is not None else None for data in results]

    @classmethod
    def from_node(cls, node: UserNode) -> Self:
        """Convert UserNode DTO to GraphQL type."""
        return cls(
            id=ID(str(node.id)),
            basic_info=UserBasicInfoGQL(
                username=node.basic_info.username,
                email=node.basic_info.email,
                full_name=node.basic_info.full_name,
                description=node.basic_info.description,
            ),
            status=UserStatusInfoGQL(
                status=UserStatusEnumGQL(node.status.status.value),
                status_info=node.status.status_info,
                need_password_change=node.status.need_password_change,
            ),
            organization=UserOrganizationInfoGQL(
                domain_name=node.organization.domain_name,
                role=UserRoleEnumGQL(node.organization.role.value)
                if node.organization.role
                else None,
                resource_policy=node.organization.resource_policy,
                main_access_key=node.organization.main_access_key,
            ),
            security=UserSecurityInfoGQL(
                allowed_client_ip=node.security.allowed_client_ip,
                totp_activated=node.security.totp_activated,
                totp_activated_at=node.security.totp_activated_at,
                sudo_session_enabled=node.security.sudo_session_enabled,
            ),
            container=UserContainerSettingsGQL(
                container_uid=node.container.container_uid,
                container_main_gid=node.container.container_main_gid,
                container_gids=node.container.container_gids,
            ),
            timestamps=EntityTimestampsGQL(
                created_at=node.timestamps.created_at,
                modified_at=node.timestamps.modified_at,
            ),
        )

    @classmethod
    def from_data(cls, data: UserData) -> Self:
        """Convert UserData to GraphQL type.

        Args:
            data: UserData instance from the data layer.

        Returns:
            UserV2GQL instance with structured field groups.
        """
        return cls(
            id=ID(str(data.id)),
            basic_info=UserBasicInfoGQL(
                username=data.username,
                email=data.email,
                full_name=data.full_name,
                description=data.description,
            ),
            status=UserStatusInfoGQL(
                status=UserStatusEnumGQL(data.status),
                status_info=data.status_info,
                need_password_change=data.need_password_change,
            ),
            organization=UserOrganizationInfoGQL(
                domain_name=data.domain_name,
                role=UserRoleEnumGQL(data.role.value) if data.role else None,
                resource_policy=data.resource_policy,
                main_access_key=data.main_access_key,
            ),
            security=UserSecurityInfoGQL(
                allowed_client_ip=data.allowed_client_ip,
                totp_activated=data.totp_activated,
                totp_activated_at=data.totp_activated_at,
                sudo_session_enabled=data.sudo_session_enabled,
            ),
            container=UserContainerSettingsGQL(
                container_uid=data.container_uid,
                container_main_gid=data.container_main_gid,
                container_gids=data.container_gids,
            ),
            timestamps=EntityTimestampsGQL(
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )


UserV2Edge = Edge[UserV2GQL]


@strawberry.type(
    description=(
        "Added in 26.2.0. Paginated connection for user records. "
        "Provides relay-style cursor-based pagination for efficient traversal of user data. "
        "Use 'edges' to access individual records with cursor information, "
        "or 'nodes' for direct data access."
    )
)
class UserV2Connection(Connection[UserV2GQL]):
    """Paginated connection for user records."""

    count: int = strawberry.field(
        description="Total number of user records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
