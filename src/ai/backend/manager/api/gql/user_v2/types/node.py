"""User V2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

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
