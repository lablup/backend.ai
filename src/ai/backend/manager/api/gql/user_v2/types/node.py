"""User V2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.gql.fair_share.types import (
    UserFairShareConnection,
    UserFairShareFilter,
    UserFairShareOrderBy,
)
from ai.backend.manager.api.gql.resource_usage.types import (
    UserUsageBucketConnection,
    UserUsageBucketFilter,
    UserUsageBucketOrderBy,
)

from .enums import UserRoleEnum, UserStatusEnum
from .nested import (
    EntityTimestampsGQL,
    UserBasicInfoGQL,
    UserContainerSettingsGQL,
    UserOrganizationInfoGQL,
    UserSecurityInfoGQL,
    UserStatusInfoGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.user.types import UserData


@strawberry.input(name="UserFairShareScope")
class UserFairShareScopeGQL:
    """Scope parameters for filtering user fair shares."""

    resource_group: str = strawberry.field(description="Resource group to filter fair shares by.")
    project_id: UUID = strawberry.field(
        description="Project ID that the user belongs to (required for user-level fair shares)."
    )


@strawberry.input(name="UserUsageScope")
class UserUsageScopeGQL:
    """Scope parameters for filtering user usage buckets."""

    resource_group: str = strawberry.field(description="Resource group to filter usage buckets by.")
    project_id: UUID = strawberry.field(
        description="Project ID that the user belongs to (required for user-level usage)."
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
class UserV2GQL(Node):
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
            "Fair share records for this user, filtered by resource group and project. "
            "Returns fair share policy specifications and calculation snapshots."
        )
    )
    async def fair_shares(
        self,
        info: Info,
        scope: UserFairShareScopeGQL,
        filter: UserFairShareFilter | None = None,
        order_by: list[UserFairShareOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> UserFairShareConnection:
        from ai.backend.manager.api.gql.fair_share.fetcher.user import (
            fetch_rg_user_fair_shares,
        )
        from ai.backend.manager.repositories.fair_share.options import (
            UserFairShareConditions,
        )
        from ai.backend.manager.repositories.fair_share.types import (
            UserFairShareSearchScope,
        )

        # Create repository scope with context information
        if self.organization.domain_name is None:
            raise InvalidAPIParameters("User must belong to a domain to query fair shares")
        repository_scope = UserFairShareSearchScope(
            resource_group=scope.resource_group,
            domain_name=self.organization.domain_name,
            project_id=scope.project_id,
        )

        # Entity-specific filter only
        base_conditions = [
            UserFairShareConditions.by_user_uuid(UUID(str(self.id))),
        ]

        return await fetch_rg_user_fair_shares(
            info=info,
            scope=repository_scope,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
            base_conditions=base_conditions,
        )

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
        from ai.backend.manager.api.gql.resource_usage.fetcher.user_usage import (
            fetch_user_usage_buckets,
        )
        from ai.backend.manager.repositories.resource_usage_history.options import (
            UserUsageBucketConditions,
        )

        base_conditions = [
            UserUsageBucketConditions.by_resource_group(scope.resource_group),
            UserUsageBucketConditions.by_user_uuid(UUID(str(self.id))),
            UserUsageBucketConditions.by_project_id(scope.project_id),
        ]

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
            base_conditions=base_conditions,
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
                status=UserStatusEnum(data.status),
                status_info=data.status_info,
                need_password_change=data.need_password_change,
            ),
            organization=UserOrganizationInfoGQL(
                domain_name=data.domain_name,
                role=UserRoleEnum(data.role.value) if data.role else None,
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
