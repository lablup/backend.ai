"""ProjectV2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.fair_share.types import ProjectFairShareGQL
from ai.backend.manager.api.gql.resource_usage.types import (
    ProjectUsageBucketConnection,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrderBy,
)

from .enums import ProjectTypeEnum, VFolderHostPermissionEnum
from .nested import (
    ProjectBasicInfoGQL,
    ProjectLifecycleInfoGQL,
    ProjectOrganizationInfoGQL,
    ProjectStorageInfoGQL,
    VFolderHostPermissionEntryGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.user_v2.types.filters import UserV2Filter, UserV2OrderBy
    from ai.backend.manager.api.gql.user_v2.types.node import UserV2Connection
    from ai.backend.manager.data.group.types import GroupData


@strawberry.input(name="ProjectFairShareScope")
class ProjectFairShareScopeGQL:
    """Scope parameters for filtering project fair shares."""

    resource_group: str = strawberry.field(description="Resource group to filter fair shares by.")


@strawberry.input(name="ProjectUsageScope")
class ProjectUsageScopeGQL:
    """Scope parameters for filtering project usage buckets."""

    resource_group: str = strawberry.field(description="Resource group to filter usage buckets by.")


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
class ProjectV2GQL(Node):
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
        from ai.backend.manager.api.gql.fair_share.fetcher.project import (
            fetch_single_project_fair_share,
        )

        return await fetch_single_project_fair_share(
            info=info,
            resource_group=scope.resource_group,
            project_id=UUID(str(self.id)),
        )

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
        from ai.backend.manager.api.gql.resource_usage.fetcher.project_usage import (
            fetch_rg_project_usage_buckets,
        )
        from ai.backend.manager.repositories.resource_usage_history.types import (
            ProjectUsageBucketSearchScope,
        )

        # Create repository scope with context information
        repository_scope = ProjectUsageBucketSearchScope(
            resource_group=scope.resource_group,
            domain_name=self.organization.domain_name,
            project_id=UUID(str(self.id)),
        )

        # No additional filters needed (scope includes all entity info)
        base_conditions = None

        return await fetch_rg_project_usage_buckets(
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
        description="The domain this project belongs to.",
    )
    async def domain(
        self,
        info: Info,
    ) -> Annotated[
        DomainV2GQL,
        strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
    ]:
        from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
        from ai.backend.manager.errors.resource import DomainNotFound

        data = await info.context.data_loaders.domain_loader.load(self.organization.domain_name)
        if data is None:
            raise DomainNotFound(self.organization.domain_name)
        return DomainV2GQL.from_data(data)

    @strawberry.field(  # type: ignore[misc]
        description="Users who are members of this project.",
    )
    async def users(
        self,
        info: Info,
        filter: Annotated[
            UserV2Filter | None,
            strawberry.lazy("ai.backend.manager.api.gql.user_v2.types.filters"),
        ] = None,
        order_by: Annotated[
            list[UserV2OrderBy] | None,
            strawberry.lazy("ai.backend.manager.api.gql.user_v2.types.filters"),
        ] = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Annotated[
        UserV2Connection,
        strawberry.lazy("ai.backend.manager.api.gql.user_v2.types.node"),
    ]:
        from ai.backend.manager.api.gql.user_v2.fetcher.user import fetch_project_users
        from ai.backend.manager.repositories.user.types import ProjectUserSearchScope

        scope = ProjectUserSearchScope(project_id=UUID(str(self.id)))
        return await fetch_project_users(
            info=info,
            scope=scope,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )

    @classmethod
    def from_data(
        cls,
        data: GroupData,
    ) -> Self:
        """Convert GroupData to GraphQL type.

        Args:
            data: GroupData instance from the data layer.

        Returns:
            ProjectV2GQL instance with structured field groups.

        Note:
            - All fields are directly from GroupRow (no external lookups)
            - VFolderHostPermissionMap (dict) is converted to list[VFolderHostPermissionEntryGQL]
            - No JSON scalars are used in the output
            - ResourceSlot and container_registry are excluded; use dedicated APIs
        """
        # Convert VFolderHostPermissionMap (dict[str, set[VFolderHostPermission]]) to list of entries
        vfolder_host_entries = [
            VFolderHostPermissionEntryGQL(
                host=host,
                permissions=[VFolderHostPermissionEnum(perm.value) for perm in perms],
            )
            for host, perms in data.allowed_vfolder_hosts.items()
        ]

        return cls(
            id=ID(str(data.id)),
            basic_info=ProjectBasicInfoGQL(
                name=data.name,
                description=data.description,
                type=ProjectTypeEnum(data.type.value),
                integration_id=data.integration_id,
            ),
            organization=ProjectOrganizationInfoGQL(
                domain_name=data.domain_name,
                resource_policy=data.resource_policy,
            ),
            storage=ProjectStorageInfoGQL(
                allowed_vfolder_hosts=vfolder_host_entries,
            ),
            lifecycle=ProjectLifecycleInfoGQL(
                is_active=data.is_active,
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )


ProjectV2Edge = Edge[ProjectV2GQL]


@strawberry.type(
    description=(
        "Added in 26.2.0. Paginated connection for project records. "
        "Provides relay-style cursor-based pagination for efficient traversal of project data. "
        "Use 'edges' to access individual records with cursor information, "
        "or 'nodes' for direct data access."
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
