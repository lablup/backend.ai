"""ProjectV2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from .enums import ProjectTypeEnum, VFolderHostPermissionEnum
from .nested import (
    ProjectBasicInfoGQL,
    ProjectLifecycleInfoGQL,
    ProjectOrganizationInfoGQL,
    ProjectStorageInfoGQL,
    VFolderHostPermissionEntryGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.group.types import GroupData


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
